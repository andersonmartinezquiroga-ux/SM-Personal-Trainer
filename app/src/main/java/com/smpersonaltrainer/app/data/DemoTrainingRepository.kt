package com.smpersonaltrainer.app.data

class DemoTrainingRepository : TrainingRepository {
    private val students = mutableListOf(
        Student("s1","Carlos Pérez","carlos@example.com","Ganar masa muscular","Intermedio",78.0),
        Student("s2","Laura Gómez","laura@example.com","Perder grasa","Inicial",64.0),
        Student("s3","Andrés Rodríguez","andres@example.com","Mejorar condición física","Avanzado",91.0)
    )

    private val workouts = listOf(
        Workout("w1","Día 1 · Pecho + Bíceps","Fuerza y desarrollo", listOf(
            Exercise("e1","Press banca plano con barra",4,"12"),
            Exercise("e2","Press banca plano con mancuernas",4,"12"),
            Exercise("e3","Press inclinado con barra",4,"12"),
            Exercise("e4","Press inclinado con mancuernas",4,"12"),
            Exercise("e5","Press declinado",4,"12"),
            Exercise("e6","Aperturas",4,"12"),
            Exercise("e7","Curl con barra",4,"12"),
            Exercise("e8","Curl con mancuerna",4,"12"),
            Exercise("e9","Curl martillo",4,"12"),
            Exercise("e10","Curl en polea",4,"12"),
            Exercise("e11","Curl con cuerda",4,"12")
        )),
        Workout("w2","Día 2 · Espalda + Tríceps","Anchura, densidad y fuerza", listOf(
            Exercise("e12","Jalón agarre cerrado",4,"12"),
            Exercise("e13","Jalón agarre abierto",4,"12"),
            Exercise("e14","Jalón agarre invertido",4,"12"),
            Exercise("e15","Máquina de remo",4,"12"),
            Exercise("e16","Máquina de espalda",4,"12"),
            Exercise("e17","Extensión de tríceps",4,"12"),
            Exercise("e18","Tríceps en polea",4,"12")
        )),
        Workout("w3","Día 3 · Piernas","Fuerza y volumen", listOf(
            Exercise("e19","Máquina jaca / hack",4,"12"),
            Exercise("e20","Leg Station",4,"12"),
            Exercise("e21","Leg Curl",4,"12"),
            Exercise("e22","Máquina Smith",4,"12"),
            Exercise("e23","Máquina aductor",4,"12"),
            Exercise("e24","Sentadilla",4,"12"),
            Exercise("e25","Tijera / zancada",4,"12")
        )),
        Workout("w4","Día 4 · Abdominales","Zona media", listOf(
            Exercise("e26","Rueda abdominal",4,"25–30"),
            Exercise("e27","Elevación de piernas",4,"25–30"),
            Exercise("e28","Abdominal corta hacia atrás",4,"25–30"),
            Exercise("e29","Abdominal con peso",4,"25–30")
        ))
    )

    private val assignments = mutableListOf(
        Assignment("a1","s1","w1","2026-08-18"),
        Assignment("a2","s2","w3","2026-08-18",true),
        Assignment("a3","s3","w2","2026-08-19")
    )

    private val progress = mutableListOf(
        ProgressEntry("p1","s1","2026-08-01",79.4,88.0,103.0,37.5),
        ProgressEntry("p2","s1","2026-08-15",78.0,86.5,104.0,38.0),
        ProgressEntry("p3","s2","2026-08-01",66.0,78.0,92.0,29.0),
        ProgressEntry("p4","s2","2026-08-15",64.0,75.5,91.0,28.5)
    )

    override fun getStudents() = students.toList()
    override fun getStudent(studentId: String) = students.find { it.id == studentId }
    override fun addStudent(student: Student) { students.add(student) }
    override fun getWorkouts() = workouts
    override fun getWorkout(workoutId: String) = workouts.find { it.id == workoutId }
    override fun getAssignments(studentId: String) = assignments.filter { it.studentId == studentId }
    override fun assignWorkout(studentId: String, workoutId: String): Assignment {
        val item = Assignment("a${assignments.size + 1}", studentId, workoutId, "2026-08-20")
        assignments.add(item)
        return item
    }
    override fun getProgress(studentId: String) = progress.filter { it.studentId == studentId }
    override fun addProgress(entry: ProgressEntry) { progress.add(entry) }
}
