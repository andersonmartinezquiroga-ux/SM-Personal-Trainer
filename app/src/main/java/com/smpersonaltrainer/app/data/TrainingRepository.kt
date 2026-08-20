package com.smpersonaltrainer.app.data

interface TrainingRepository {
    fun getStudents(): List<Student>
    fun getStudent(studentId: String): Student?
    fun addStudent(student: Student)
    fun getWorkouts(): List<Workout>
    fun getWorkout(workoutId: String): Workout?
    fun getAssignments(studentId: String): List<Assignment>
    fun assignWorkout(studentId: String, workoutId: String): Assignment
    fun getProgress(studentId: String): List<ProgressEntry>
    fun addProgress(entry: ProgressEntry)
}
