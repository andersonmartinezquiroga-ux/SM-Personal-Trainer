import unreal
from datetime import datetime

def log(msg):
    unreal.log("[SJM AUTOPILOT] " + msg)

def ensure_folder(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)
        log("Carpeta creada: " + path)

def ensure_actor_blueprint(asset_path, variables):
    bp = unreal.EditorAssetLibrary.load_asset(asset_path)
    if not bp:
        bp = unreal.BlueprintEditorLibrary.create_blueprint_asset_with_parent(asset_path, unreal.Actor)
        if not bp:
            raise RuntimeError("No se pudo crear " + asset_path)
        log("Blueprint creado: " + asset_path)
    else:
        log("Blueprint encontrado: " + asset_path)

    existing = set(str(x) for x in unreal.BlueprintEditorLibrary.list_member_variable_names(bp, False))
    for name, kind in variables:
        if name not in existing:
            pin_type = unreal.BlueprintEditorLibrary.get_basic_type_by_name(kind)
            if not unreal.BlueprintEditorLibrary.add_member_variable(bp, name, pin_type):
                raise RuntimeError("No se pudo crear variable " + name + " en " + asset_path)
            log("Variable creada: " + asset_path + " :: " + name)

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    if not unreal.EditorAssetLibrary.save_loaded_asset(bp, False):
        raise RuntimeError("No se pudo guardar " + asset_path)
    log("Blueprint compilado y guardado: " + asset_path)

ensure_folder("/Game/sjm/core")
ensure_folder("/Game/sjm/exercises")

ensure_actor_blueprint(
    "/Game/sjm/core/BP_SJMCoreController",
    [
        ("bSystemReady", "bool"),
        ("bSessionActive", "bool"),
        ("CurrentUserId", "string"),
        ("CurrentSessionId", "string"),
        ("CurrentExerciseId", "string"),
        ("CurrentModule", "string"),
        ("TotalSessionReps", "int"),
        ("SessionScore", "real"),
        ("FatigueIndex", "real"),
        ("PainFlag", "bool"),
        ("AIEnabled", "bool"),
        ("LastSystemMessage", "string"),
    ],
)

ensure_actor_blueprint(
    "/Game/sjm/exercises/BP_SJMExerciseSession",
    [
        ("ExerciseId", "string"),
        ("ExerciseName", "string"),
        ("TargetReps", "int"),
        ("CompletedReps", "int"),
        ("SetNumber", "int"),
        ("TargetSets", "int"),
        ("RestSeconds", "real"),
        ("TempoLabel", "string"),
        ("RangeScore", "real"),
        ("TechniqueScore", "real"),
        ("SessionElapsedTime", "real"),
        ("bExerciseComplete", "bool"),
    ],
)

unreal.EditorAssetLibrary.save_directory("/Game/sjm", False, True)
log("SJM TASK 002 completada " + datetime.now().isoformat())
