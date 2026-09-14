package com.smpersonaltrainer.app

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.smpersonaltrainer.app.data.*

private val Black = Color(0xFF050505)
private val Dark = Color(0xFF111111)
private val Gold = Color(0xFFD9B63E)
private val LightGold = Color(0xFFFFE080)
private val White = Color(0xFFF7F7F7)
private val Gray = Color(0xFFB7B7B7)

data class Module(val id: String, val title: String, val subtitle: String, val icon: ImageVector)

private val modules = listOf(
    Module("coach", "SM PERFORMANCE 360", "Panel del entrenador, alumnos y asignación", Icons.Default.Dashboard),
    Module("library", "BIBLIOTECA DE EJERCICIOS", "Grupos musculares, técnica y músculos trabajados", Icons.Default.FitnessCenter),
    Module("programs", "PROGRAMAS Y RUTINAS", "Hipertrofia, definición, fuerza, movilidad y core", Icons.Default.Assignment),
    Module("nutrition", "NUTRICIÓN", "Planes, recetas y programación semanal", Icons.Default.Restaurant),
    Module("functional", "ENTRENAMIENTO FUNCIONAL", "TRX, kickboxing, CrossFit y circuitos", Icons.Default.SportsMartialArts),
    Module("senior", "ADULTO MAYOR", "Rutinas seguras de fuerza, equilibrio y movilidad", Icons.Default.AccessibilityNew),
    Module("injuries", "LESIONES Y ADAPTACIONES", "Rodilla, espalda, hombro, codo y cadera", Icons.Default.HealthAndSafety),
    Module("progress", "PROGRESO", "Medidas, peso, objetivos y seguimiento", Icons.Default.ShowChart),
    Module("plans", "PLANES Y PAGOS", "Servicios online y presenciales", Icons.Default.Payments),
    Module("ai", "SM IA", "Consulta de entrenamiento y orientación general", Icons.Default.AutoAwesome),
    Module("social", "CONTACTO Y REDES", "WhatsApp, Instagram, Facebook y TikTok", Icons.Default.Share)
)

@Composable
fun SMTheme(content: @Composable () -> Unit) = MaterialTheme(
    colorScheme = darkColorScheme(primary = Gold, secondary = LightGold, background = Black, surface = Dark),
    content = content
)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { SMTheme { SMApp() } }
    }
}

@Composable
fun SMApp() {
    val repo = remember { DemoTrainingRepository() }
    var screen by remember { mutableStateOf("home") }
    var studentId by remember { mutableStateOf<String?>(null) }
    BackHandler(screen != "home" || studentId != null) {
        if (studentId != null) studentId = null else screen = "home"
    }
    when {
        studentId != null -> StudentScreen(repo, studentId!!) { studentId = null }
        screen == "home" -> HomeScreen { screen = it }
        screen == "coach" -> CoachDashboard(repo, { studentId = it }, { screen = "workouts" }, { screen = "home" })
        screen == "workouts" -> WorkoutsScreen(repo) { screen = "coach" }
        else -> ModuleScreen(screen, repo) { screen = "home" }
    }
}

@Composable
fun HomeScreen(onOpen: (String) -> Unit) {
    LazyColumn(
        Modifier.fillMaxSize().background(Brush.verticalGradient(listOf(Color(0xFF171000), Black, Black))).padding(horizontal = 18.dp),
        verticalArrangement = Arrangement.spacedBy(13.dp), contentPadding = PaddingValues(top = 28.dp, bottom = 32.dp)
    ) {
        item {
            Text("♛  SM", color = Gold, fontSize = 32.sp, fontWeight = FontWeight.Black)
            Text("PERSONAL TRAINER", color = White, fontSize = 30.sp, fontWeight = FontWeight.Black)
            Text("ENTRENA CONMIGO ESTÉS DONDE ESTÉS", color = LightGold, fontSize = 13.sp, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(9.dp))
            Text("Entrenamiento personalizado online desde cualquier país", color = Gray, fontSize = 17.sp)
        }
        item {
            Card(colors = CardDefaults.cardColors(Color(0xFF191407)), shape = RoundedCornerShape(20.dp), modifier = Modifier.border(1.dp, Gold, RoundedCornerShape(20.dp))) {
                Column(Modifier.padding(18.dp)) {
                    Text("SAMUEL MARTÍNEZ", color = Gold, fontSize = 22.sp, fontWeight = FontWeight.Black)
                    Text("Rutinas personalizadas para gimnasio o casa", color = White)
                    Text("Seguimiento semanal por videollamada", color = Gray)
                }
            }
        }
        item { Text("TODOS LOS SERVICIOS", color = White, fontSize = 22.sp, fontWeight = FontWeight.Black) }
        items(modules.chunked(2)) { pair ->
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                pair.forEach { module -> ModuleCard(module, Modifier.weight(1f)) { onOpen(module.id) } }
                if (pair.size == 1) Spacer(Modifier.weight(1f))
            }
        }
        item {
            Text("“Todo lo puedo en Cristo que me fortalece”", Modifier.fillMaxWidth().padding(top = 10.dp), color = LightGold, textAlign = TextAlign.Center, fontWeight = FontWeight.Bold)
        }
    }
}

@Composable
fun ModuleCard(module: Module, modifier: Modifier, onClick: () -> Unit) {
    Card(modifier.height(158.dp).clickable(onClick = onClick).border(1.dp, Color(0xFF6E5817), RoundedCornerShape(18.dp)), colors = CardDefaults.cardColors(Dark), shape = RoundedCornerShape(18.dp)) {
        Column(Modifier.fillMaxSize().padding(14.dp), verticalArrangement = Arrangement.SpaceBetween) {
            Icon(module.icon, null, tint = Gold, modifier = Modifier.size(30.dp))
            Column {
                Text(module.title, color = White, fontWeight = FontWeight.Black, fontSize = 14.sp)
                Text(module.subtitle, color = Gray, fontSize = 11.sp, lineHeight = 14.sp)
            }
        }
    }
}

@Composable
fun ModuleScreen(id: String, repo: TrainingRepository, onBack: () -> Unit) {
    val module = modules.first { it.id == id }
    val content = when (id) {
        "library" -> listOf(
            "PECHO" to "Press plano, inclinado y declinado; aperturas y fondos.",
            "ESPALDA" to "Jalones abiertos, cerrados e invertidos; remos y dominadas.",
            "PIERNAS Y GLÚTEOS" to "Sentadilla, hack, prensa, curl femoral, aductores y zancadas.",
            "HOMBROS" to "Press militar, elevaciones laterales, frontales y posteriores.",
            "BÍCEPS Y TRÍCEPS" to "Curl barra, predicador, martillo, polea y extensiones.",
            "CORE Y ABDOMEN" to "Rueda, elevación de piernas, abdominal corta y con peso."
        )
        "programs" -> listOf("HIPERTROFIA" to "Volumen progresivo por grupos musculares.", "DEFINICIÓN" to "Fuerza, circuitos y control nutricional.", "PÉRDIDA DE PESO" to "Progresión cardiovascular y fuerza adaptada.", "FUERZA" to "Técnica, cargas y recuperación.", "MOVILIDAD Y CORE" to "Estabilidad, rango de movimiento y control.")
        "nutrition" -> listOf("GANAR MASA" to "Superávit moderado, proteína suficiente y seguimiento.", "PERDER GRASA" to "Déficit progresivo conservando fuerza y masa muscular.", "RECETAS" to "Desayunos, almuerzos, cenas y snacks.", "PLAN SEMANAL" to "Programación organizada y lista de compras.", "SUPLEMENTOS" to "Proteína, creatina, aminoácidos y L-carnitina con uso responsable.")
        "functional" -> listOf("TRX" to "Empujes, remos, sentadillas y core en suspensión.", "KICKBOXING" to "Guardia, desplazamientos, golpes y combinaciones.", "CROSSFIT" to "Movimientos funcionales escalables y técnica.", "CIRCUITO DE RESISTENCIA" to "Estaciones por tiempo y nivel.")
        "senior" -> listOf("FUERZA SEGURA" to "Sentarse y levantarse, empujes y tracciones adaptadas.", "EQUILIBRIO" to "Apoyos, marcha y estabilidad con asistencia.", "MOVILIDAD" to "Rutinas suaves y progresivas.", "PLAN INICIAL" to "2–3 sesiones semanales según valoración profesional.")
        "injuries" -> listOf("RODILLA" to "Alternativas sin dolor y progresión controlada.", "ESPALDA" to "Estabilidad del tronco y movimientos tolerados.", "HOMBRO" to "Movilidad y fuerza dentro de rango cómodo.", "CODO" to "Ajustes de agarre, carga y volumen.", "CADERA" to "Movilidad, estabilidad y fortalecimiento progresivo.")
        "progress" -> listOf("MEDIDAS" to "Peso, cintura, pecho, brazo y fotografías.", "OBJETIVOS" to "Metas concretas y revisión semanal.", "CALENDARIO" to "Sesiones, asistencia y videollamadas.", "EVOLUCIÓN" to "Comparación de registros y ajustes del programa.")
        "plans" -> listOf("PRESENCIAL" to "$62.000 COP por clase.", "ONLINE" to "$50.000 COP por clase.", "PAQUETES" to "Planes mensuales personalizados.", "INCLUYE" to "Rutina, seguimiento y ajustes según progreso.")
        "ai" -> listOf("CONSULTA SM IA" to "Preguntas generales de entrenamiento, técnica, rutinas y hábitos.", "SEGURIDAD" to "La orientación no reemplaza diagnóstico médico ni nutricional.")
        "social" -> listOf("WHATSAPP" to "Contacto directo con SM Personal Trainer.", "INSTAGRAM" to "Entrenamiento, consejos y novedades.", "FACEBOOK" to "Comunidad y servicios.", "TIKTOK" to "Contenido fitness y técnica.")
        else -> emptyList()
    }
    val context = LocalContext.current
    LazyColumn(Modifier.fillMaxSize().background(Black).padding(horizontal = 18.dp), verticalArrangement = Arrangement.spacedBy(12.dp), contentPadding = PaddingValues(top = 20.dp, bottom = 30.dp)) {
        item { Header(module.title, module.subtitle, onBack) }
        items(content) { (title, description) ->
            Card(colors = CardDefaults.cardColors(Dark), shape = RoundedCornerShape(17.dp), modifier = Modifier.fillMaxWidth().border(1.dp, Color(0xFF5B4917), RoundedCornerShape(17.dp))) {
                Row(Modifier.padding(17.dp), verticalAlignment = Alignment.CenterVertically) {
                    Icon(module.icon, null, tint = Gold)
                    Spacer(Modifier.width(13.dp))
                    Column { Text(title, color = Gold, fontWeight = FontWeight.Black, fontSize = 17.sp); Text(description, color = White, fontSize = 14.sp) }
                }
            }
        }
        if (id == "social") item {
            Button({ context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("https://wa.me/573337002626"))) }, Modifier.fillMaxWidth(), colors = ButtonDefaults.buttonColors(Gold)) {
                Icon(Icons.Default.Chat, null, tint = Black); Spacer(Modifier.width(8.dp)); Text("ABRIR WHATSAPP", color = Black, fontWeight = FontWeight.Black)
            }
        }
        if (id == "programs") item {
            OutlinedButton({ }, Modifier.fillMaxWidth(), colors = ButtonDefaults.outlinedButtonColors(contentColor = Gold)) { Text("RUTINAS DISPONIBLES: ${repo.getWorkouts().size}") }
        }
    }
}

@Composable
fun Header(title: String, subtitle: String, onBack: () -> Unit) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        IconButton(onBack) { Icon(Icons.Default.ArrowBack, "Atrás", tint = Gold) }
        Column { Text(title, color = Gold, fontSize = 24.sp, fontWeight = FontWeight.Black); Text(subtitle, color = Gray, fontSize = 13.sp) }
    }
}

@Composable
fun CoachDashboard(repo: TrainingRepository, onStudent: (String) -> Unit, onWorkouts: () -> Unit, onBack: () -> Unit) {
    var refresh by remember { mutableIntStateOf(0) }; var showAdd by remember { mutableStateOf(false) }; val students = remember(refresh) { repo.getStudents() }
    LazyColumn(Modifier.fillMaxSize().background(Black).padding(18.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { Header("SM PERFORMANCE 360", "Panel profesional del entrenador", onBack) }
        item { Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) { Stat("ALUMNOS", students.size.toString(), Modifier.weight(1f)); Stat("ACTIVOS", students.count { it.active }.toString(), Modifier.weight(1f)); Stat("RUTINAS", repo.getWorkouts().size.toString(), Modifier.weight(1f)) } }
        item { Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) { Button({ showAdd = true }, Modifier.weight(1f), colors = ButtonDefaults.buttonColors(Gold)) { Text("+ ALUMNO", color = Black, fontWeight = FontWeight.Black) }; OutlinedButton(onWorkouts, Modifier.weight(1f)) { Text("RUTINAS", color = Gold) } } }
        item { Text("MIS ALUMNOS", color = White, fontSize = 21.sp, fontWeight = FontWeight.Black) }
        items(students) { s -> Card(Modifier.fillMaxWidth().clickable { onStudent(s.id) }, colors = CardDefaults.cardColors(Dark), shape = RoundedCornerShape(16.dp)) { Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) { Icon(Icons.Default.Person, null, tint = Gold); Spacer(Modifier.width(12.dp)); Column(Modifier.weight(1f)) { Text(s.name, color = White, fontWeight = FontWeight.Bold); Text(s.goal, color = Gray); Text(s.level, color = Gray, fontSize = 12.sp) }; Text(s.weightKg?.let { "$it kg" } ?: "—", color = Gold, fontWeight = FontWeight.Black) } } }
    }
    if (showAdd) AddStudentDialog({ showAdd = false }) { name, email, goal -> repo.addStudent(Student("s${repo.getStudents().size + 1}", name, email, goal, "Inicial", null)); refresh++; showAdd = false }
}

@Composable
fun StudentScreen(repo: TrainingRepository, studentId: String, onBack: () -> Unit) {
    val student = repo.getStudent(studentId) ?: return; val assignments = repo.getAssignments(studentId); val progress = repo.getProgress(studentId)
    LazyColumn(Modifier.fillMaxSize().background(Black).padding(18.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        item { Header(student.name, student.email, onBack) }
        item { Info("OBJETIVO", student.goal); Info("NIVEL", student.level); Info("PESO", student.weightKg?.let { "$it kg" } ?: "Sin registrar") }
        item { Text("RUTINAS ASIGNADAS", color = Gold, fontWeight = FontWeight.Black) }
        items(assignments) { a -> val w = repo.getWorkout(a.workoutId); Info(w?.title ?: "Rutina", if (a.completed) "COMPLETADA" else "PENDIENTE") }
        item { Text("PROGRESO", color = Gold, fontWeight = FontWeight.Black) }
        items(progress.reversed()) { p -> Info(p.date, "Peso ${p.weightKg ?: "—"} kg · Cintura ${p.waistCm ?: "—"} cm") }
    }
}

@Composable
fun WorkoutsScreen(repo: TrainingRepository, onBack: () -> Unit) {
    LazyColumn(Modifier.fillMaxSize().background(Black).padding(18.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { Header("RUTINAS", "Programación SM Personal Trainer", onBack) }
        items(repo.getWorkouts()) { w -> Card(colors = CardDefaults.cardColors(Dark), shape = RoundedCornerShape(16.dp)) { Column(Modifier.fillMaxWidth().padding(16.dp)) { Text(w.title, color = Gold, fontWeight = FontWeight.Black, fontSize = 18.sp); Text(w.subtitle, color = Gray); Spacer(Modifier.height(8.dp)); w.exercises.forEach { Text("• ${it.name} · ${it.sets} × ${it.reps}", color = White, fontSize = 14.sp) } } } }
    }
}

@Composable
fun AddStudentDialog(onDismiss: () -> Unit, onAdd: (String, String, String) -> Unit) {
    var name by remember { mutableStateOf("") }; var email by remember { mutableStateOf("") }; var goal by remember { mutableStateOf("") }
    AlertDialog(onDismissRequest = onDismiss, title = { Text("Nuevo alumno") }, text = { Column { OutlinedTextField(name, { name = it }, label = { Text("Nombre") }); OutlinedTextField(email, { email = it }, label = { Text("Correo") }); OutlinedTextField(goal, { goal = it }, label = { Text("Objetivo") }) } }, confirmButton = { TextButton({ if (name.isNotBlank()) onAdd(name, email, goal) }) { Text("AGREGAR", color = Gold) } }, dismissButton = { TextButton(onDismiss) { Text("CANCELAR") } })
}

@Composable
fun Info(label: String, value: String) { Card(colors = CardDefaults.cardColors(Dark), shape = RoundedCornerShape(14.dp)) { Column(Modifier.fillMaxWidth().padding(15.dp)) { Text(label, color = Gold, fontSize = 12.sp, fontWeight = FontWeight.Black); Text(value, color = White, fontSize = 17.sp, fontWeight = FontWeight.Bold) } }; Spacer(Modifier.height(7.dp)) }

@Composable
fun Stat(label: String, value: String, modifier: Modifier) { Card(modifier, colors = CardDefaults.cardColors(Dark), shape = RoundedCornerShape(14.dp)) { Column(Modifier.padding(12.dp)) { Text(label, color = Gray, fontSize = 9.sp); Text(value, color = Gold, fontSize = 23.sp, fontWeight = FontWeight.Black) } } }
