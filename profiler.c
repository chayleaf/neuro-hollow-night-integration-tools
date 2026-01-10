#define _GNU_SOURCE
#include <dlfcn.h>
#include <link.h>
#include <mono/metadata/debug-helpers.h>
#include <mono/metadata/profiler-legacy.h>
#include <mono/metadata/profiler.h>
#include <mono/metadata/threads.h>
#include <stdatomic.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <threads.h>
#include <time.h>

#define HOOKS                                                                  \
  HOOK(mono_method_full_name);                                                 \
  HOOK(mono_thread_current);                                                   \
  HOOK(mono_profiler_install);                                                 \
  HOOK(mono_profiler_set_events);                                              \
  HOOK(mono_profiler_install_enter_leave);                                     \
  HOOK(mono_gc_get_used_size);

#define HOOK(name) static typeof(name) *p_##name;
HOOKS
#undef HOOK

struct StackEntry {
  MonoMethod *method;
  struct timespec time;
};

struct MetInfo {
  MonoMethod *met;
  struct timespec acc;
};

struct MetTable {
  struct MetTable *next;
  int cnt;
  int cap;
  struct MetInfo *i;
};

static thread_local struct StackEntry stack[65536];
static thread_local struct MetTable *tab;
static thread_local int stackp = 0;
static struct MetTable *_Atomic tables;

static inline struct MetInfo *insert_met(struct MetInfo *i, int cap,
                                         MonoMethod *method) {
  uintptr_t pos = ((uintptr_t)method >> 8) +
                  ((uintptr_t)method << (sizeof(uintptr_t) * 8 - 8));

  struct MetInfo *info = &i[pos & (cap - 1)];
  while (info->met) {
    if (info->met == method)
      return info;
    ++pos;
    info = &i[pos & (cap - 1)];
  }
  return info;
}

static inline struct MetInfo *find_met(struct MetTable **tab,
                                       MonoMethod *method, bool add_next) {
  if (!method)
    return NULL;
  // struct MetBin *bin = &method_bins[((intptr_t)method >> 8) & 0xFFFF];
  if (!*tab) {
    *tab = malloc(sizeof(struct MetTable));
    (*tab)->i = calloc(1024, sizeof(struct MetInfo));
    (*tab)->cap = 1024;
    (*tab)->cnt = 0;
    if (add_next) {
      (*tab)->next = atomic_load(&tables);
      struct MetTable *exp = (*tab)->next;
      while (!atomic_compare_exchange_strong(&tables, &exp, *tab)) {
        (*tab)->next = atomic_load(&tables);
        exp = (*tab)->next;
      }
    }
  }
  struct MetInfo *info = insert_met((*tab)->i, (*tab)->cap, method);
  if (info->met == method)
    return info;
  // insert
  if ((*tab)->cnt * 2 >= (*tab)->cap) {
    // resize & rebalance
    // dont even free, will only save factor of 2 mem usage
    struct MetInfo *i2 = calloc((*tab)->cap * 2, sizeof(struct MetInfo));
    for (int i = 0; i < (*tab)->cap; ++i) {
      if (!(*tab)->i[i].met)
        continue;
      struct MetInfo *info = insert_met(i2, (*tab)->cap * 2, (*tab)->i[i].met);
      *info = (*tab)->i[i];
    }
    info = insert_met(i2, (*tab)->cap * 2, method);
    // non-thread safe, but i don't really care
    (*tab)->cap *= 2;
    (*tab)->i = i2;
  }
  info->met = method;
  ++(*tab)->cnt;
  return info;
}

static void profiler_enter(MonoLegacyProfiler *prof, MonoMethod *method) {
  if (stackp >= sizeof(stack) / sizeof(stack[0]))
    return;
  struct StackEntry *e = &stack[stackp++];
  e->method = method;
  clock_gettime(CLOCK_THREAD_CPUTIME_ID, &e->time);
}

static void profiler_leave(MonoLegacyProfiler *prof, MonoMethod *method) {
  if (stackp <= 0)
    return;
  --stackp;
  if (stack[stackp].method != method)
    return;
  struct timespec time;
  clock_gettime(CLOCK_THREAD_CPUTIME_ID, &time);
  struct MetInfo *i = find_met(&tab, method, true);
  i->acc.tv_nsec += time.tv_nsec;
  i->acc.tv_sec += time.tv_sec;
  i->acc.tv_nsec -= stack[stackp].time.tv_nsec;
  i->acc.tv_sec -= stack[stackp].time.tv_sec;
  if (i->acc.tv_nsec < 0) {
    i->acc.tv_nsec += 1000000000;
    i->acc.tv_sec -= 1;
  } else if (i->acc.tv_nsec >= 1000000000) {
    i->acc.tv_nsec -= 1000000000;
    i->acc.tv_sec += 1;
  }
}

static struct timespec timer_res;

static bool init_done;
static int dl_iterator(struct dl_phdr_info *info, size_t size, void *data) {
  if (!strstr(info->dlpi_name, "libmono"))
    return 0;
  clock_getres(CLOCK_THREAD_CPUTIME_ID, &timer_res);
  FILE *f = fopen("state.txt", "w");
  if (!f)
    return 1;
  fprintf(f, "dlopen %s\n", info->dlpi_name);
  void *h = dlopen(info->dlpi_name, RTLD_LAZY | RTLD_NOLOAD);
  fprintf(f, "dlopen returned %p\n", h);
  if (!h) {
    fprintf(f, "err dlopening %s\n", info->dlpi_name);
    goto done;
  }
#define HOOK(name)                                                             \
  p_##name = dlsym(h, #name);                                                  \
  if (!p_##name) {                                                             \
    fputs("err dlsym " #name "\n", f);                                         \
    goto done;                                                                 \
  } else {                                                                     \
    fprintf(f, "dlsym " #name " returned %p\n", p_##name);                     \
  }
  HOOKS
#undef HOOK
  p_mono_profiler_install(NULL, NULL);
  p_mono_profiler_install_enter_leave(profiler_enter, profiler_leave);
  p_mono_profiler_set_events(1 << 12);
  fputs("load done\n", f);
  init_done = true;
done:
  fclose(f);
  return 1;
}

void profiler_reset() {
  // non thread safe
  if (!init_done)
    dl_iterate_phdr(dl_iterator, NULL);
  for (volatile struct MetTable *tab = atomic_load(&tables); tab;
       tab = tab->next) {
    int cap = tab->cap;
    struct MetInfo *p = tab->i;
    for (int i = 0; i < cap; ++i) {
      p[i].acc.tv_nsec = 0;
      p[i].acc.tv_sec = 0;
    }
  }
}

void profiler_save() {
  int t = time(NULL);
  char s[256];
  sprintf(s, "out%d.txt", t);
  FILE *f = fopen(s, "w");
  if (!f)
    return;
  struct MetTable *join = NULL;
  // minor data race safeguard (not guaranteed but better than nothing)
  for (volatile struct MetTable *tab = atomic_load(&tables); tab;
       tab = tab->next) {
    int cap = tab->cap;
    struct MetInfo *p = tab->i;
    for (int i = 0; i < cap; ++i) {
      if (!p[i].met)
        continue;
      struct MetInfo *target = find_met(&join, p[i].met, false);
      target->acc.tv_nsec += p[i].acc.tv_nsec;
      target->acc.tv_sec += p[i].acc.tv_sec;
      if (target->acc.tv_nsec >= 1000000000) {
        target->acc.tv_nsec -= 1000000000;
        target->acc.tv_sec += 1;
      }
    }
  }
  if (join) {
    for (int i = 0; i < join->cap; ++i) {
      if (!join->i[i].met)
        continue;
      fprintf(f, "%ld.%09ld %s\n", join->i[i].acc.tv_sec, join->i[i].acc.tv_nsec,
              p_mono_method_full_name(join->i[i].met, false));
    }
  }
  fclose(f);
}
