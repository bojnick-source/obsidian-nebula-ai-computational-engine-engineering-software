import type { ViewerPlugin } from "../../../types/viewer";
import type { AssetRecord } from "../../../types/asset";
import type { BufferGeometry, Group, Object3D, WebGLRenderer } from "three";

const CAD_MIMES = [
  "model/stl",
  "model/gltf-binary",
  "model/gltf+json",
  "application/octet-stream", // fallback for STL
];

const CAD_EXTENSIONS = [".stl", ".glb", ".gltf", ".obj"];

interface ThreeScene {
  renderer: WebGLRenderer;
  animationId: number;
}

let activeScene: ThreeScene | null = null;

export const ThreeViewerPlugin: ViewerPlugin = {
  id: "three-viewer",
  displayName: "3D Model Viewer",
  supportedMimeTypes: CAD_MIMES,
  priority: 30,

  canRender(asset: AssetRecord): boolean {
    if (CAD_MIMES.includes(asset.fileType)) return true;
    const lc = asset.originalName.toLowerCase();
    return CAD_EXTENSIONS.some((ext) => lc.endsWith(ext));
  },

  async renderPreview(
    container: HTMLElement,
    asset: AssetRecord,
    objectUrl: string
  ): Promise<void> {
    container.innerHTML = "";
    container.style.background = "#0a0a14";
    container.style.position = "relative";

    const THREE = await import("three");
    const { OrbitControls } = await import(
      "three/examples/jsm/controls/OrbitControls.js"
    );

    const width = container.clientWidth || 800;
    const height = container.clientHeight || 600;

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setClearColor(0x0a0a14);
    container.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.add(new THREE.AmbientLight(0xffffff, 0.6));
    const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
    dirLight.position.set(5, 10, 7);
    scene.add(dirLight);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.01, 10000);
    camera.position.set(3, 3, 3);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;

    const ext = asset.originalName.toLowerCase().split(".").pop();

    const fitCamera = (object: Object3D) => {
      const box = new THREE.Box3().setFromObject(object);
      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3()).length();
      controls.target.copy(center);
      camera.position.copy(center).addScalar(size * 0.8);
    };

    if (ext === "stl") {
      const { STLLoader } = await import(
        "three/examples/jsm/loaders/STLLoader.js"
      );
      const loader = new STLLoader();
      const geometry = await new Promise<BufferGeometry>((resolve, reject) =>
        loader.load(objectUrl, resolve, undefined, reject)
      );
      geometry.computeVertexNormals();
      const mat = new THREE.MeshPhongMaterial({
        color: 0x3a82f6,
        specular: 0x222244,
        shininess: 60,
      });
      const mesh = new THREE.Mesh(geometry, mat);
      scene.add(mesh);
      fitCamera(mesh);
    } else if (ext === "glb" || ext === "gltf") {
      const { GLTFLoader } = await import(
        "three/examples/jsm/loaders/GLTFLoader.js"
      );
      const loader = new GLTFLoader();
      const gltf = await new Promise<{ scene: Group }>((resolve, reject) =>
        loader.load(objectUrl, resolve as never, undefined, reject)
      );
      scene.add(gltf.scene);
      fitCamera(gltf.scene);
    } else if (ext === "obj") {
      const { OBJLoader } = await import(
        "three/examples/jsm/loaders/OBJLoader.js"
      );
      const loader = new OBJLoader();
      const obj = await new Promise<Group>((resolve, reject) =>
        loader.load(objectUrl, resolve, undefined, reject)
      );
      scene.add(obj);
      fitCamera(obj);
    }

    controls.update();

    let animationId = 0;
    function animate() {
      animationId = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    }
    animate();

    activeScene = { renderer, animationId };

    // Handle resize
    const resizeObserver = new ResizeObserver(() => {
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    });
    resizeObserver.observe(container);
    // Attach observer reference for cleanup
    (renderer.domElement as HTMLCanvasElement & { _resizeObserver?: ResizeObserver })._resizeObserver = resizeObserver;
  },

  async renderThumbnail(_asset: AssetRecord): Promise<Blob> {
    const canvas = document.createElement("canvas");
    canvas.width = 128;
    canvas.height = 96;
    const ctx = canvas.getContext("2d")!;
    ctx.fillStyle = "#0a1020";
    ctx.fillRect(0, 0, 128, 96);
    ctx.strokeStyle = "rgba(58,130,246,0.7)";
    ctx.lineWidth = 1.5;
    ctx.strokeRect(30, 24, 48, 48);
    ctx.beginPath();
    ctx.moveTo(30, 24);
    ctx.lineTo(50, 10);
    ctx.lineTo(98, 10);
    ctx.lineTo(78, 24);
    ctx.moveTo(98, 10);
    ctx.lineTo(98, 58);
    ctx.lineTo(78, 72);
    ctx.stroke();
    ctx.fillStyle = "rgba(255,255,255,0.4)";
    ctx.font = "bold 9px sans-serif";
    ctx.fillText("3D", 56, 85);
    return new Promise((resolve, reject) =>
      canvas.toBlob((b) => (b ? resolve(b) : reject(new Error("canvas.toBlob returned null"))), "image/png")
    );
  },

  dispose(): void {
    if (activeScene) {
      cancelAnimationFrame(activeScene.animationId);
      const domEl = activeScene.renderer.domElement as HTMLCanvasElement & { _resizeObserver?: ResizeObserver };
      domEl._resizeObserver?.disconnect();
      activeScene.renderer.dispose();
      activeScene = null;
    }
  },
};
