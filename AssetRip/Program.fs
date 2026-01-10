open AssetsTools.NET
open AssetsTools.NET.Extra

let manager = new AssetsManager()
let pkg = manager.LoadClassPackage "classdata.tpk" |> ignore

if manager.ClassPackage = null then
    raise (System.Exception())

let gameBase =
    "/data/data/Games/SteamLibrary/steamapps/common/Hollow Knight/hollow_knight_Data"

let fileInst0 = manager.LoadAssetsFile(sprintf "%s/resources.assets" gameBase)

let file0 = fileInst0.file
manager.LoadClassDatabaseFromPackage file0.Metadata.UnityVersion |> ignore

if manager.ClassDatabase = null then
    raise (System.Exception())

manager.MonoTempGenerator <- MonoCecilTempGenerator(sprintf "%s/Managed" gameBase)

let mbNameFast (fileInst: AssetsFileInstance) (info: AssetFileInfo) =
    try
        if
            info.GetTypeId fileInst.file <> int AssetClassID.MonoBehaviour
            && info.TypeId >= 0
        then
            None
        else
            let monoTemp =
                manager.GetTemplateBaseField(fileInst, info, AssetReadFlags.SkipMonoBehaviourFields).Clone()

            let nameIndex = monoTemp.Children.FindIndex(_.Name >> (=) "m_Script")

            if nameIndex <> -1 then
                monoTemp.Children.RemoveRange(nameIndex + 1, monoTemp.Children.Count - (nameIndex + 1))

            lock fileInst.LockReader (fun () ->
                monoTemp.MakeValue(fileInst.file.Reader, info.GetAbsoluteByteOffset fileInst.file))
            |> Option.ofObj
            |> Option.bind (fun monoBf -> manager.GetExtAsset(fileInst, monoBf["m_Script"]).baseField |> Option.ofObj)
            |> Option.map (fun scriptBaseField -> scriptBaseField["m_ClassName"].AsString)
    with _ ->
        None

let assetName fileInst fileId pathId =
    (if fileId = 0 && pathId = 0 then None else Some())
    |> Option.bind (fun () ->
        let external =
            manager.GetExtAsset(fileInst, fileId, pathId, true, AssetReadFlags.SkipMonoBehaviourFields)

        let extInfo = external.info
        let extFileInst = external.file
        let extFile = extFileInst.file

        let classId = extInfo.GetTypeId extFile

        let read typeName childIsName =
            let reader = extFile.Reader

            if childIsName then
                lock extFileInst.LockReader (fun () ->
                    reader.Position <- extInfo.GetAbsoluteByteOffset extFile
                    reader.ReadCountStringInt32() |> Option.ofObj |> Option.filter ((<>) ""))
            else if typeName = "GameObject" then
                lock extFileInst.LockReader (fun () ->
                    reader.Position <- extInfo.GetAbsoluteByteOffset extFile
                    let size = reader.ReadInt32()

                    let componentSize =
                        if extFile.Header.Version > uint32 0x10 then
                            0x0c: int64
                        else
                            0x10

                    reader.Position <- reader.Position + int64 size * componentSize + (0x04: int64)
                    reader.ReadCountStringInt32() |> Option.ofObj |> Option.filter ((<>) ""))
            else if typeName = "MonoBehaviour" then
                lock extFileInst.LockReader (fun () ->
                    reader.Position <- extInfo.GetAbsoluteByteOffset extFile + (0x1C: int64)

                    reader.ReadCountStringInt32()
                    |> Option.ofObj
                    |> Option.filter ((<>) "")
                    |> Option.orElseWith (fun () -> mbNameFast fileInst extInfo |> Option.filter ((<>) "")))
            else
                None

        match
            if extFile.Metadata.TypeTreeEnabled then
                if classId = 0x72 || classId < 0 then
                    extFile.Metadata.FindTypeTreeTypeByScriptIndex(extInfo.GetScriptIndex extFile)
                else
                    extFile.Metadata.FindTypeTreeTypeByID classId
                |> Option.ofObj
                |> Option.filter (fun x -> x.Nodes.Count > 0)
            else
                None
        with
        | Some ttType ->
            let typeName = ttType.Nodes[0].GetTypeString ttType.StringBufferBytes
            let reader = extFile.Reader

            read
                typeName
                (ttType.Nodes.Count > 1
                 && ttType.Nodes[1].GetNameString ttType.StringBufferBytes = "m_Name")
        | None ->
            Option.ofObj manager.ClassDatabase
            |> Option.bind (fun cldb ->
                cldb.FindAssetClassByID classId
                |> Option.ofObj
                |> Option.map (fun typ -> cldb, typ))
            |> Option.bind (fun (cldb, typ) ->
                let typeName = cldb.GetString typ.Name
                let cldbNodes = typ.GetPreferredNode(false).Children

                if cldbNodes.Count = 0 then
                    None
                else
                    read typeName (cldbNodes.Count > 1 && cldb.GetString(cldbNodes[0].FieldName) = "m_Name")))

type AssetValue =
    | ABool of bool
    | AI8 of int8
    | AI16 of int16
    | AI32 of int32
    | AI64 of int64
    | AU8 of uint8
    | AU16 of uint16
    | AU32 of uint32
    | AU64 of uint64
    | AF32 of float32
    | AF64 of float
    | AS of string
    | AB of byte array
    | AArr of AssetValue array
    | AObj of (string * AssetValue) array

let rec toJson lvl av =
    match av with
    | ABool true -> "true"
    | ABool false -> "false"
    | AI8 x -> $"{x}"
    | AI16 x -> $"{x}"
    | AI32 x -> $"{x}"
    | AI64 x -> $"{x}"
    | AU8 x -> $"{x}"
    | AU16 x -> $"{x}"
    | AU32 x -> $"{x}"
    | AU64 x -> $"{x}"
    | AF32 x -> $"{x}"
    | AF64 x -> $"{x}"
    | AS x ->
         "\"" + String.collect (fun c -> match c with
                                         | '\\' -> "\\\\"
                                         | '\n' -> "\\n"
                                         | '\r' -> "\\r"
                                         | '\b' -> "\\b"
                                         | '\f' -> "\\f"
                                         | '\t' -> "\\t"
                                         | '"' -> "\\\""
                                         | c when c < ' ' -> "\u" + int(c).ToString "X4"
                                         | c -> $"{c}") x + "\""
        //"\"" + x.Replace("\\", "\\\\").Replace("\n", "\\n").Replace("\r", "\\r").Replace("\"", "\\\"") + "\""
    | AB x ->
        "\""
        + String.concat "" (x |> Array.map (fun n -> "\\u" + n.ToString "X4"))
        + "\""
    | AArr x ->
        if Array.length x = 0 then
            "[]"
        else if Array.length x = 1 then
            $"[{toJson lvl (x[0])}]"
        else
            let ident = String.replicate lvl "  "
            let ident1 = String.replicate (lvl + 1) "  "

            $"[\n{ident1}"
            + String.concat $",\n{ident1}" (x |> Array.map (toJson (lvl + 1)))
            + $"\n{ident}]"
    | AObj x ->
        if Array.length x = 0 then
            "{}"
        else
            let ident = String.replicate lvl "  "
            let ident1 = String.replicate (lvl + 1) "  "

            "{"
            + $"\n{ident1}"
            + String.concat $",\n{ident1}" (x |> Array.map (fun (k, v) -> $"{toJson 0 (AS k)}: {toJson (lvl + 1) v}"))
            + $"\n{ident}"
            + "}"

let mutable cycles = Set.empty

let rec dumpObj depth (fileInst: AssetsFileInstance) (obj: AssetTypeValueField) =
    let value = obj.Value

    if value = null then
        let vals =
            obj
            |> Array.ofSeq
            |> Array.filter (fun x -> x.TemplateField.Name <> "m_FontData")

        if
            depth <> 0
            && vals.Length = 2
            && (vals[0].TemplateField.Name = "m_FileID"
                && vals[1].TemplateField.Name = "m_PathID"
                || vals[0].TemplateField.Name = "m_PathID"
                   && vals[1].TemplateField.Name = "m_FileID")
        then
            let fid, pid =
                if vals[0].TemplateField.Name = "m_FileID" then
                    vals[0], vals[1]
                else
                    vals[1], vals[0]

            let fid = fid.AsInt
            let pid = pid.AsInt

            if fid = 0 && pid <> 860 then
                let info = fileInst.file.GetAssetInfo pid

                if info = null || Set.contains (fileInst.path, info.ByteOffset) cycles then
                    let vals =
                        vals |> Array.map (fun x -> x.TemplateField.Name, dumpObj depth fileInst x)

                    AObj vals
                else
                    dumpAsset depth fileInst info |> snd
            else
                let asset = manager.GetExtAsset(fileInst, fid, pid)

                if
                    pid = 860
                    || asset.info = null
                    || Set.contains (asset.file.path, asset.info.ByteOffset) cycles
                then
                    let vals =
                        vals |> Array.map (fun x -> x.TemplateField.Name, dumpObj depth fileInst x)

                    AObj vals
                else
                    dumpAsset depth asset.file asset.info |> snd
        else
            let vals =
                vals |> Array.map (fun x -> x.TemplateField.Name, dumpObj depth fileInst x)

            AObj vals
    else
        match value.ValueType with
        | AssetValueType.UInt8 -> AU8 value.AsByte
        | AssetValueType.Int8 -> AI8 value.AsSByte
        | AssetValueType.UInt16 -> AU16 value.AsUShort
        | AssetValueType.Int16 -> AI16 value.AsShort
        | AssetValueType.UInt32 -> AU32 value.AsUInt
        | AssetValueType.Int32 -> AI32 value.AsInt
        | AssetValueType.UInt64 -> AU64 value.AsULong
        | AssetValueType.Int64 -> AI64 value.AsLong
        | AssetValueType.Float -> AF32 value.AsFloat
        | AssetValueType.Double -> AF64 value.AsDouble
        | AssetValueType.String -> AS value.AsString
        | AssetValueType.ByteArray -> AB value.AsByteArray
        | AssetValueType.Array -> AArr(Array.init obj.AsArray.size (obj.Get >> dumpObj depth fileInst))
        | AssetValueType.Bool -> ABool value.AsBool
        | x -> raise (System.Exception $"not supported: {x}")

and dumpAsset depth fileInst (ainfo: AssetFileInfo) =
    cycles <- Set.add (fileInst.path, ainfo.ByteOffset) cycles
    let tpl = manager.GetTemplateBaseField(fileInst, ainfo)
    // let asset = manager.GetExtAsset(fileInst, 0, ainfo.PathId)
    let v = manager.GetBaseField(fileInst, ainfo) // asset.baseField

    let tryHyph x =
        try
            let x = x ()
            if x = "" then "" else sprintf " - %s" x
        with _ ->
            ""

    let fname =
        sprintf
            "%d%s%s%s"
            ainfo.PathId
            (tryHyph (fun () -> v["m_Name"].AsString))
            (tryHyph (fun () ->
                let go = v["m_GameObject"]
                assetName fileInst (go["m_FileID"].AsInt) (go["m_PathID"].AsInt) |> Option.get))
            (tryHyph (fun () ->
                let vFsm = v["fsm"]
                vFsm["name"].AsString))

    printfn "%s" fname

    // printf "%s" $"{toJson 0 (dumpObj v)}"
    fname, dumpObj (depth - 1) fileInst v

System.IO.Directory.EnumerateFiles gameBase
|> Seq.filter (fun x -> (x.EndsWith "resources.assets"))
|> Seq.iter (fun fpath ->
    printfn "%s" fpath
    let fname = System.IO.Path.GetFileName fpath

    try
        let fileInst = manager.LoadAssetsFile(sprintf "%s/%s" gameBase fname)
        // printfn "%s" (fileInst.file.Metadata.Externals |> List.ofSeq |> List.map (fun x -> x.PathName) |> String.concat "; ")
        Some fileInst
    with _ ->
        printfn "fail"
        None
    |> Option.iter (fun fileInst ->
        let file = fileInst.file
        let out = $"out/{fname}"
        System.IO.Directory.CreateDirectory out |> ignore

        file.AssetInfos
        // |> Seq.filter (_.TypeId >> (=) (int AssetClassID.MonoBehaviour))
        // |> Seq.skipWhile (_.PathId >> (>=) 3896)
        // |> Seq.skip 16498
        |> Seq.iter (fun x ->
            try
                cycles <- Set.empty
                let name, v = dumpAsset 1 fileInst x
                System.IO.File.WriteAllText($"{out}/{name}.json", toJson 0 v)
            with e ->
                printfn "%d error %s" x.PathId (e.ToString()))))
