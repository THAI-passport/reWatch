plugins {
    kotlin("jvm") version "2.0.21"
}

repositories { mavenCentral() }

dependencies {
    testImplementation(kotlin("test"))
}

kotlin { jvmToolchain(21) }

tasks.test {
    useJUnitPlatform()
    // Shared byte vectors produced by the Python reference (client/c900/vectors.py).
    systemProperty("c900.vectors", rootDir.resolve("../../tests/fixtures/c900_vectors.json").absolutePath)
}
