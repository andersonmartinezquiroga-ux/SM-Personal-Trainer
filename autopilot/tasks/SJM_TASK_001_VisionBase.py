import unreal
from datetime import datetime

BP_PATH = "/Game/sjm/motion360/vision/BP_SJMVisionController"

def log(msg):
    unreal.log("[SJM AUTOPILOT] " + msg)

folders = [
    "/Game/sjm/core",
    "/Game/sjm/motion360",
    "/Game/sjm/motion360/vision",
    "/Game/sjm/ui",
    "/Game/sjm/exercises",
    "/Game/sjm/data",
    "/Game/sjm/ai",
    "/Game/sjm/avatars",
    "/Game/sjm/progress",
    "/Game/sjm/sensors",
]

for folder in folders:
    if not unreal.EditorAssetLibrary.does_directory_exist(folder):
        unreal.EditorAssetLibrary.make_directory(folder)
        log("Carpeta creada: " + folder)

bp = unreal.EditorAssetLibrary.load_asset(BP_PATH)
if not bp:
    bp = unreal.BlueprintEditorLibrary.create_blueprint_asset_with_parent(BP_PATH, unreal.Actor)
    if not bp:
        raise RuntimeError("No se pudo crear BP_SJMVisionController")
    log("BP_SJMVisionController creado")
else:
    log("BP_SJMVisionController encontrado")

specs = [
    ("bEvaluationActive", "bool"),
    ("RepCount", "int"),
    ("CurrentPhase", "string"),
    ("Confidence", "real"),
    ("KneeAngleEstimated", "real"),
    ("HipAngleEstimated", "real"),
    ("TrunkInclinationEstimated", "real"),
    ("SessionElapsedTime", "real"),
    ("LastRepDuration", "real"),
]

existing = set(str(x) for x in unreal.BlueprintEditorLibrary.list_member_variable_names(bp, False))
for name, kind in specs:
    if name not in existing:
        pin_type = unreal.BlueprintEditorLibrary.get_basic_type_by_name(kind)
        if not unreal.BlueprintEditorLibrary.add_member_variable(bp, name, pin_type):
            raise RuntimeError("No se pudo crear variable: " + name)
        log("Variable creada: " + name)

unreal.BlueprintEditorLibrary.compile_blueprint(bp)
if not unreal.EditorAssetLibrary.save_loaded_asset(bp, False):
    raise RuntimeError("No se pudo guardar BP_SJMVisionController")

unreal.EditorAssetLibrary.save_directory("/Game/sjm", False, True)
log("SJM TASK 001 completada " + datetime.now().isoformat())
