package dev.mcmusic.app.ui.design

import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

/** Pure-Kotlin geometry checks: no Compose runtime or Android view is needed. */
class BlobShapeTest {
    @Test
    fun everyGeneratedPathHasSaneBounds() {
        assertTrue("no generated blobs", BlobShapes.paths.isNotEmpty())
        for ((id, source) in BlobShapes.paths) {
            val geometry = parseBlobPath(source)
            assertTrue("$id has no commands", geometry.commands.isNotEmpty())
            assertTrue("$id has no width", geometry.width > 10f)
            assertTrue("$id has no height", geometry.height > 10f)
            assertTrue("$id starts left of 0", geometry.minX >= -1f)
            assertTrue("$id starts above 0", geometry.minY >= -1f)
            assertTrue("$id ends right of 100", geometry.maxX <= 101f)
            assertTrue("$id ends below 100", geometry.maxY <= 101f)
        }
    }

    @Test
    fun arcBlobIsApproximatedWithCubics() {
        val geometry = parseBlobPath(BlobShapes.paths.getValue("blob-1"))
        assertTrue("arc blob has no cubic segments", geometry.commands.any { it is BlobCommand.Cubic })
    }

    @Test
    fun everyBlobIdProducesAShape() {
        for (id in BlobShapes.ids) {
            assertNotNull("$id has no shape", blobShape(id))
        }
    }
}
