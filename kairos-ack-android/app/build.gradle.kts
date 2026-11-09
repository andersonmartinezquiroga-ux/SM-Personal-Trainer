plugins { id("com.android.application") }

android {
    namespace = "com.sjm.kairosbridge"
    compileSdk = 35
    defaultConfig {
        applicationId = "com.sjm.kairosbridge"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
