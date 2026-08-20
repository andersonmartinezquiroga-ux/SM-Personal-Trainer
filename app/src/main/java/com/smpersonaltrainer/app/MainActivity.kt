package com.smpersonaltrainer.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.smpersonaltrainer.app.data.*

private val Black = Color(0xFF080808)
private val Dark = Color(0xFF121212)
private val Gold = Color(0xFFD4AF37)
private val White = Color(0xFFF7F7F7)
private val Gray = Color(0xFFAAAAAA)

@Composable
fun SMTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = darkColorScheme(
            primary = Gold, secondary = Gold, background = Black,
            surface = Dark, onPrimary = Black, onBackground = White, onSurface = White
        ),
        content = content
    )
}

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { SMTheme { SMApp() } }
    }
}

@Composable
fun SMApp() {
    val repo = remember { DemoTrainingRepository() }
    var selectedStudentId by remember { mutableStateOf<String?>(null) }
    var screen by remember { mutableStateOf("coach") }

    when {
        selectedStudentId != null -> StudentScreen(repo, selectedStudentId!!) { selectedStudentId = null }
        screen == "coach" -> CoachDashboard(repo, { selectedStudentId = it }, { screen = "workouts" })
        else -> WorkoutsScreen(repo) { screen = "coach" }
    }
}

@Composable
fun CoachDashboard(
    repo: TrainingRepository,
    onStudent: (String) -> Unit,
    onWorkouts: () -> Unit
) {
    var refresh by remember { mutableIntStateOf(0) }
    var showAdd by remember { mutableStateOf(false) }
    val students = remember(refresh) { repo.getStudents() }

    LazyColumn(
        Modifier.fillMaxSize().background(Black).padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item {
            Text("PANEL DEL ENTRENADOR", color = Gold, fontSize = 28.sp, fontWeight = FontWeight.Black)
            Text("Samuel Martínez · SM Personal Trainer", color = Gray)
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Stat("ALUMNOS", students.size.toString(), Modifier.weight(1f))
                Stat("ACTIVOS", students.count { it.active }.toString(), Modifier.weight(1f))
                Stat("RUTINAS", repo.getWorkouts().size.toString(), Modifier.weight(1f))
            }
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(
                    { showAdd = true },
                    Modifier.weight(1f),
                    colors = ButtonDefaults.buttonColors(Gold)
                ) { Text("+ ALUMNO", color = Black, fontWeight = FontWeight.Black) }

                OutlinedButton(
                    onWorkouts,
                    Modifier.weight(1f),
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = Gold)
                ) { Text("RUTINAS") }
            }
        }
        item { Text("MIS ALUMNOS", color = White, fontSize = 20.sp, fontWeight = FontWeight.Bold) }
        items(students) { s ->
            Card(
                Modifier.fillMaxWidth().clickable { onStudent(s.id) },
                colors = CardDefaults.cardColors(Dark),
                shape = RoundedCornerShape(16.dp)
            ) {
                Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.Person, null, tint = Gold)
                    Spacer(Modifier.width(12.dp))
                    Column(Modifier.weight(1f)) {
                        Text(s.name, color = White, fontWeight = FontWeight.Bold)
                        Text(s.goal, color = Gray, fontSize = 13.sp)
                        Text(s.level, color = Gray, fontSize = 12.sp)
                    }
                    Text(s.weightKg?.let { "$it kg" } ?: "—", color = Gold, fontWeight = FontWeight.Black)
                }
            }
        }
    }

    if (showAdd) {
        AddStudentDialog(
            onDismiss = { showAdd = false },
            onAdd = { name, email, goal ->
                repo.addStudent(
                    Student(
                        "s${repo.getStudents().size + 1}",
                        name, email, goal, "Inicial", null
                    )
                )
                refresh++
                showAdd = false
            }
        )
    }
}

@Composable
fun StudentScreen(repo: TrainingRepository, studentId: String, onBack: () -> Unit) {
    var refresh by remember { mutableIntStateOf(0) }
    var showAssign by remember { mutableStateOf(false) }
    var showProgress by remember { mutableStateOf(false) }

    val student = repo.getStudent(studentId) ?: return
    val assignments = remember(refresh) { repo.getAssignments(studentId) }
    val progress = remember(refresh) { repo.getProgress(studentId) }

    LazyColumn(
        Modifier.fillMaxSize().background(Black).padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item {
            Row(verticalAlignment = Alignment.CenterVertically) {
                IconButton(onBack) { Icon(Icons.Default.ArrowBack, "Atrás", tint = White) }
                Column {
                    Text(student.name, color = Gold, fontSize = 26.sp, fontWeight = FontWeight.Black)
                    Text(student.email, color = Gray)
                }
            }
        }
        item {
            Info("OBJETIVO", student.goal)
            Info("NIVEL", student.level)
            Info("PESO ACTUAL", student.weightKg?.let { "$it kg" } ?: "Sin registrar")
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(
                    { showAssign = true },
                    Modifier.weight(1f),
                    colors = ButtonDefaults.buttonColors(Gold)
                ) { Text("ASIGNAR RUTINA", color = Black, fontWeight = FontWeight.Black) }

                OutlinedButton(
                    { showProgress = true },
                    Modifier.weight(1f),
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = Gold)
                ) { Text("+ PROGRESO") }
            }
        }
        item { Text("RUTINAS ASIGNADAS", color = White, fontSize = 19.sp, fontWeight = FontWeight.Bold) }
        if (assignments.isEmpty()) {
            item { Text("Todavía no hay rutinas asignadas.", color = Gray) }
        } else {
            items(assignments) { a ->
                val workout = repo.getWorkout(a.workoutId)
                Card(colors = CardDefaults.cardColors(Dark), shape = RoundedCornerShape(14.dp)) {
                    Column(Modifier.fillMaxWidth().padding(15.dp)) {
                        Text(workout?.title ?: "Rutina", color = White, fontWeight = FontWeight.Bold)
                        Text("Asignada: ${a.assignedDate}", color = Gray)
                        Text(if (a.completed) "COMPLETADA" else "PENDIENTE", color = Gold, fontWeight = FontWeight.Black)
                    }
                }
            }
        }
        item { Text("PROGRESO", color = White, fontSize = 19.sp, fontWeight = FontWeight.Bold) }
        if (progress.isEmpty()) {
            item { Text("No hay registros todavía.", color = Gray) }
        } else {
            items(progress.reversed()) { p ->
                Card(colors = CardDefaults.cardColors(Dark), shape = RoundedCornerShape(14.dp)) {
                    Column(Modifier.fillMaxWidth().padding(15.dp)) {
                        Text(p.date, color = Gold, fontWeight = FontWeight.Bold)
                        Text("Peso: ${p.weightKg ?: "—"} kg", color = White)
                        Text("Cintura: ${p.waistCm ?: "—"} cm", color = Gray)
                        Text("Pecho: ${p.chestCm ?: "—"} cm", color = Gray)
                        Text("Brazo: ${p.armCm ?: "—"} cm", color = Gray)
                    }
                }
            }
        }
    }

    if (showAssign) {
        AssignWorkoutDialog(
            repo.getWorkouts(),
            { showAssign = false },
            {
                repo.assignWorkout(studentId, it)
                refresh++
                showAssign = false
            }
        )
    }

    if (showProgress) {
        AddProgressDialog(
            studentId,
            { showProgress = false },
            {
                repo.addProgress(it)
                refresh++
                showProgress = false
            }
        )
    }
}

@Composable
fun WorkoutsScreen(repo: TrainingRepository, onBack: () -> Unit) {
    LazyColumn(
        Modifier.fillMaxSize().background(Black).padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item {
            Row(verticalAlignment = Alignment.CenterVertically) {
                IconButton(onBack) { Icon(Icons.Default.ArrowBack, "Atrás", tint = White) }
                Text("RUTINAS", color = Gold, fontSize = 28.sp, fontWeight = FontWeight.Black)
            }
        }
        items(repo.getWorkouts()) { w ->
            Card(colors = CardDefaults.cardColors(Dark), shape = RoundedCornerShape(16.dp)) {
                Column(Modifier.fillMaxWidth().padding(16.dp)) {
                    Text(w.title, color = White, fontWeight = FontWeight.Bold)
                    Text(w.subtitle, color = Gray)
                    Text("${w.exercises.size} ejercicios", color = Gold, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

@Composable
fun AddStudentDialog(onDismiss: () -> Unit, onAdd: (String, String, String) -> Unit) {
    var name by remember { mutableStateOf("") }
    var email by remember { mutableStateOf("") }
    var goal by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Nuevo alumno") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(name, { name = it }, label = { Text("Nombre") })
                OutlinedTextField(email, { email = it }, label = { Text("Correo") })
                OutlinedTextField(goal, { goal = it }, label = { Text("Objetivo") })
            }
        },
        confirmButton = {
            TextButton({ if (name.isNotBlank()) onAdd(name, email, goal) }) {
                Text("AGREGAR", color = Gold)
            }
        },
        dismissButton = { TextButton(onDismiss) { Text("CANCELAR") } }
    )
}

@Composable
fun AssignWorkoutDialog(workouts: List<Workout>, onDismiss: () -> Unit, onAssign: (String) -> Unit) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Asignar rutina") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                workouts.forEach { w ->
                    Card(
                        Modifier.fillMaxWidth().clickable { onAssign(w.id) },
                        colors = CardDefaults.cardColors(Dark)
                    ) {
                        Column(Modifier.padding(12.dp)) {
                            Text(w.title, color = White, fontWeight = FontWeight.Bold)
                            Text(w.subtitle, color = Gray)
                        }
                    }
                }
            }
        },
        confirmButton = {},
        dismissButton = { TextButton(onDismiss) { Text("CERRAR") } }
    )
}

@Composable
fun AddProgressDialog(studentId: String, onDismiss: () -> Unit, onAdd: (ProgressEntry) -> Unit) {
    var weight by remember { mutableStateOf("") }
    var waist by remember { mutableStateOf("") }
    var chest by remember { mutableStateOf("") }
    var arm by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Registrar progreso") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(weight, { weight = it }, label = { Text("Peso kg") })
                OutlinedTextField(waist, { waist = it }, label = { Text("Cintura cm") })
                OutlinedTextField(chest, { chest = it }, label = { Text("Pecho cm") })
                OutlinedTextField(arm, { arm = it }, label = { Text("Brazo cm") })
            }
        },
        confirmButton = {
            TextButton({
                onAdd(
                    ProgressEntry(
                        "p${System.currentTimeMillis()}",
                        studentId,
                        "2026-08-20",
                        weight.toDoubleOrNull(),
                        waist.toDoubleOrNull(),
                        chest.toDoubleOrNull(),
                        arm.toDoubleOrNull()
                    )
                )
            }) { Text("GUARDAR", color = Gold) }
        },
        dismissButton = { TextButton(onDismiss) { Text("CANCELAR") } }
    )
}

@Composable
fun Info(label: String, value: String) {
    Card(colors = CardDefaults.cardColors(Dark), shape = RoundedCornerShape(14.dp)) {
        Column(Modifier.fillMaxWidth().padding(15.dp)) {
            Text(label, color = Gold, fontSize = 11.sp, fontWeight = FontWeight.Black)
            Text(value, color = White, fontSize = 18.sp, fontWeight = FontWeight.Bold)
        }
    }
    Spacer(Modifier.height(8.dp))
}

@Composable
fun Stat(label: String, value: String, modifier: Modifier) {
    Card(modifier, colors = CardDefaults.cardColors(Dark), shape = RoundedCornerShape(14.dp)) {
        Column(Modifier.padding(12.dp)) {
            Text(label, color = Gray, fontSize = 9.sp)
            Text(value, color = Gold, fontSize = 22.sp, fontWeight = FontWeight.Black)
        }
    }
}
