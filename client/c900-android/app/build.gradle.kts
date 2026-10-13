plugins {
    id("com.android.application")
    kotlin("android")
}

android {
    namespace = "rewatch.c900.app"
    compileSdk = 35

    defaultConfig {
        applicationId = "rewatch.c900.app"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_21
        targetCompatibility = JavaVersion.VERSION_21
    }
}

kotlin {
    jvmToolchain(21)
}

repositories {
    google()
    mavenCentral()
}

dependencies {
    implementation(project(":core"))

    testImplementation(kotlin("test"))
    testImplementation("junit:junit:4.13.2")
}
