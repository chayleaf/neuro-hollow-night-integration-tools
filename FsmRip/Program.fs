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
    | AS x -> "\"" + x.Replace("\\", "\\\\").Replace("\n", "\\n").Replace("\r", "\\r") + "\""
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

let dumpFsm fileInst out (ainfo: AssetFileInfo) =
    let rec dumpObj (obj: AssetTypeValueField) =

        let value = obj.Value

        if value = null then
            let vals = obj |> Seq.map (fun x -> x.TemplateField.Name, dumpObj x) |> Array.ofSeq

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
            | AssetValueType.Array -> AArr(Array.init obj.AsArray.size (obj.Get >> dumpObj))
            | x -> raise (System.Exception $"not supported: {x}")

    let tpl = manager.GetTemplateBaseField(fileInst, ainfo)
    // let asset = manager.GetExtAsset(fileInst, 0, ainfo.PathId)
    let v = manager.GetBaseField(fileInst, ainfo) // asset.baseField

    let vFsm = v["fsm"]
    let name = vFsm["name"].AsString
    let go = v["m_GameObject"]

    let fname =
        sprintf
            "%s - %s"
            (assetName fileInst (go["m_FileID"].AsInt) (go["m_PathID"].AsInt)
             |> Option.defaultValue "Unknown")
            name

    printfn "%s" fname

    // printf "%s" $"{toJson 0 (dumpObj v)}"
    System.IO.File.WriteAllText($"{out}/{fname}.json", toJson 0 (dumpObj v))

    ()

System.IO.Directory.EnumerateFiles gameBase
|> Seq.iter (fun fpath ->
    printfn "%s" fpath
    let fname = System.IO.Path.GetFileName fpath

    try
        let fileInst = manager.LoadAssetsFile(sprintf "%s/%s" gameBase fname)
        Some fileInst
    with _ ->
        None
    |> Option.iter (fun fileInst ->
        let file = fileInst.file
        let out = $"out/{fname}"
        System.IO.Directory.CreateDirectory out |> ignore

        let keys =
            AssetHelper.GetAssetsFileScriptInfos(manager, fileInst)
            |> Seq.filter (_.Value.AsmName >> (=) "PlayMaker.dll")
            |> Seq.filter (_.Value.Namespace >> (=) "")
            |> Seq.filter (_.Value.ClassName >> (=) "PlayMakerFSM")
            |> Seq.map _.Key
            |> Seq.filter ((<>) 65535)
            |> Set.ofSeq

        file.AssetInfos
        |> Seq.filter (_.TypeId >> (=) (int AssetClassID.MonoBehaviour))
        |> Seq.filter (_.GetScriptIndex(file) >> int >> keys.Contains)
        |> Seq.iter (dumpFsm fileInst out)))
