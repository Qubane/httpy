from pyodide.ffi import to_js
from pyscript import when, window, document
from js import Math, THREE, performance, Object
import asyncio


"""
Taken from PyScript.com@examples page "WebGL Icosahedron"
And made it follow PEP8 a bit more. That code still looks painful tho
"""


mouse = THREE.Vector2.new()

renderer = THREE.WebGLRenderer.new({"antialias": True})
renderer.shadowMap.enabled = False
renderer.shadowMap.type = THREE.PCFSoftShadowMap
renderer.shadowMap.needsUpdate = True

document.body.appendChild(renderer.domElement)


@when("mousemove", "body")
def on_mouse_move(event):
    event.preventDefault()
    mouse.x = (event.clientX / window.innerWidth) * 2 - 1
    mouse.y = -(event.clientY / window.innerHeight) * 2 + 1


camera = THREE.PerspectiveCamera.new(35, window.innerWidth / window.innerHeight, 1, 500)
scene = THREE.Scene.new()
cameraRange = 3

camera.aspect = window.innerWidth / window.innerHeight
camera.updateProjectionMatrix()
renderer.setSize(window.innerWidth, window.innerHeight * 0.89)

setcolor = "#000000"

scene.background = THREE.Color.new(setcolor)
scene.fog = THREE.Fog.new(setcolor, 2.5, 3.5)

sceneGroup = THREE.Object3D.new()
particularGroup = THREE.Object3D.new()


def math_random(num=1):
    return -Math.random() * num + Math.random() * num


modular_group = THREE.Object3D.new()

perms = {"flatShading": True, "color": "#111111", "transparent": False, "opacity": 1, "wireframe": False}
perms = Object.fromEntries(to_js(perms))

particle_perms = {"color": "#FFFFFF", "side": THREE.DoubleSide}
particle_perms = Object.fromEntries(to_js(particle_perms))


def create_cubes(math_random, modular_group):
    i = 0
    while i < 30:
        geometry = THREE.IcosahedronGeometry.new()
        material = THREE.MeshStandardMaterial.new(perms)
        cube = THREE.Mesh.new(geometry, material)
        cube.speedRotation = Math.random() * 0.1
        cube.positionX = math_random()
        cube.positionY = math_random()
        cube.positionZ = math_random()
        cube.castShadow = True
        cube.receiveShadow = True
        new_scale_value = math_random(0.3)
        cube.scale.set(new_scale_value,new_scale_value,new_scale_value)
        cube.rotation.x = math_random(180 * Math.PI / 180)
        cube.rotation.y = math_random(180 * Math.PI / 180)
        cube.rotation.z = math_random(180 * Math.PI / 180)
        cube.position.set(cube.positionX, cube.positionY, cube.positionZ)
        modular_group.add(cube)
        i += 1


create_cubes(math_random, modular_group)


def generateParticle(math_random, particular_group, num, amp=2):
    gmaterial = THREE.MeshPhysicalMaterial.new(particle_perms)
    gparticular = THREE.CircleGeometry.new(0.2,5)
    i = 0
    while i < num:
        pscale = 0.001+Math.abs(math_random(0.03))
        particular = THREE.Mesh.new(gparticular, gmaterial)
        particular.position.set(math_random(amp), math_random(amp), math_random(amp))
        particular.rotation.set(math_random(), math_random(), math_random())
        particular.scale.set(pscale,pscale,pscale)
        particular.speedValue = math_random(1)
        particular_group.add(particular)
        i += 1


generateParticle(math_random, particularGroup, 200, 2)

sceneGroup.add(particularGroup)
scene.add(modular_group)
scene.add(sceneGroup)

camera.position.set(0, 0, cameraRange)
cameraValue = False

ambientLight = THREE.AmbientLight.new(0xFFFFFF, 0.1)

light = THREE.SpotLight.new(0xFFFFFF, 3)
light.position.set(5, 5, 2)
light.castShadow = True
light.shadow.mapSize.width = 10000
light.shadow.mapSize.height = light.shadow.mapSize.width
light.penumbra = 0.5

lightBack = THREE.PointLight.new(0x0FFFFF, 1)
lightBack.position.set(0, -3, -1)

scene.add(sceneGroup)
scene.add(light)
scene.add(lightBack)

rectSize = 2
intensity = 14
rectLight = THREE.RectAreaLight.new(0x0FFFFF, intensity,  rectSize, rectSize)
rectLight.position.set(0, 0, 1)
rectLight.lookAt(0, 0, 0)
scene.add(rectLight)

raycaster = THREE.Raycaster.new()
uSpeed = 0.1

time = 0.0003
camera.lookAt(scene.position)


async def main():
    while True:
        time_ = performance.now() * 0.0003
        i = 0
        while i < particularGroup.children.length:
            new_object = particularGroup.children[i]
            new_object.rotation.x += new_object.speedValue/10
            new_object.rotation.y += new_object.speedValue/10
            new_object.rotation.z += new_object.speedValue/10
            i += 1

        i = 0
        while i < modular_group.children.length:
            new_cubes = modular_group.children[i]
            new_cubes.rotation.x += 0.008
            new_cubes.rotation.y += 0.005
            new_cubes.rotation.z += 0.003

            new_cubes.position.x = Math.sin(time_ * new_cubes.positionZ) * new_cubes.positionY
            new_cubes.position.y = Math.cos(time_ * new_cubes.positionX) * new_cubes.positionZ
            new_cubes.position.z = Math.sin(time_ * new_cubes.positionY) * new_cubes.positionX
            i += 1

        particularGroup.rotation.y += 0.005

        modular_group.rotation.y -= ((mouse.x * 4) + modular_group.rotation.y) * uSpeed
        modular_group.rotation.x -= ((-mouse.y * 4) + modular_group.rotation.x) * uSpeed

        renderer.render(scene, camera)
        await asyncio.sleep(0.02)


asyncio.ensure_future(main())
