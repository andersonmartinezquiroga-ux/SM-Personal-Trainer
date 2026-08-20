package com.smpersonaltrainer.app.data

data class Student(
    val id: String,
    val name: String,
    val email: String,
    val goal: String,
    val level: String,
    val weightKg: Double?,
    val active: Boolean = true
)

data class Exercise(
    val id: String,
    val name: String,
    val sets: Int,
    val reps: String
)

data class Workout(
    val id: String,
    val title: String,
    val subtitle: String,
    val exercises: List<Exercise>
)

data class Assignment(
    val id: String,
    val studentId: String,
    val workoutId: String,
    val assignedDate: String,
    val completed: Boolean = false
)

data class ProgressEntry(
    val id: String,
    val studentId: String,
    val date: String,
    val weightKg: Double?,
    val waistCm: Double?,
    val chestCm: Double?,
    val armCm: Double?
)
