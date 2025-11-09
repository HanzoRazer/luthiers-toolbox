<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'

type Span = { x1:number,y1:number,z1?:number, x2:number,y2:number,z2?:number }
const props = defineProps<{ spans: Span[], height?: number }>()

let renderer:any, scene:any, camera:any, controls:any, raf=0
const el = ref<HTMLDivElement|null>(null)

async function boot(){
  const THREE = await import('three')
  const {OrbitControls} = await import('three/examples/jsm/controls/OrbitControls.js')
  renderer = new THREE.WebGLRenderer({antialias:true})
  renderer.setSize(el.value!.clientWidth, props.height ?? 420)
  el.value!.appendChild(renderer.domElement)
  camera = new THREE.PerspectiveCamera(45, el.value!.clientWidth/(props.height ?? 420), 0.1, 10000)
  camera.position.set(0,0,300)
  // @ts-ignore
  controls = new OrbitControls(camera, renderer.domElement)
  scene = new THREE.Scene(); scene.background = new THREE.Color(0xffffff)
  const amb = new THREE.AmbientLight(0xffffff,1.0); scene.add(amb)
  draw(THREE, props.spans)
  const loop = ()=>{ raf=requestAnimationFrame(loop); controls.update(); renderer.render(scene, camera) }
  loop()
}

function draw(THREE:any, spans:Span[]){
  // remove old lines
  for(let i=scene.children.length-1;i>=0;i--){
    const o = scene.children[i]; if((o as any).isLine) scene.remove(o)
  }
  const matCut = new THREE.LineBasicMaterial({})
  const matTrav = new THREE.LineDashedMaterial({dashSize:1,gapSize:1})
  const cut = new THREE.BufferGeometry(); const trav = new THREE.BufferGeometry()
  const a:number[] = [], b:number[] = []
  for(const s of spans){
    const z1=s.z1??0, z2=s.z2??0
    const arr = (z1<=0||z2<=0) ? a : b
    arr.push(s.x1, -s.y1, z1, s.x2, -s.y2, z2)
  }
  cut.setAttribute('position', new THREE.Float32BufferAttribute(a,3))
  trav.setAttribute('position', new THREE.Float32BufferAttribute(b,3))
  scene.add(new THREE.LineSegments(cut, matCut))
  const lt = new THREE.LineSegments(trav, matTrav); lt.computeLineDistances?.(); scene.add(lt)
}

onMounted(boot)
onBeforeUnmount(()=>cancelAnimationFrame(raf))
watch(()=>props.spans, async (v)=>{ const THREE = await import('three'); draw(THREE, v||[]) })
</script>

<template>
  <div ref="el" class="w-full border rounded overflow-hidden"></div>
</template>
