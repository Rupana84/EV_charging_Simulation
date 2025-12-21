import { Suspense, useEffect, useMemo, useRef } from "react";
import { Canvas } from "@react-three/fiber";
import { Environment, OrbitControls, useGLTF } from "@react-three/drei";
import {
  ACESFilmicToneMapping,
  Box3,
  SRGBColorSpace,
  Vector3,
} from "three";

const CAR_MODEL_URL = "/models/2020_polestar_2.glb";

function CarModel({ rotationAngle }) {
  const groupRef = useRef(null);
  const { scene } = useGLTF(CAR_MODEL_URL);

  const { alignedModel, offset, scale } = useMemo(() => {
    const clone = scene.clone(true);
    const box = new Box3().setFromObject(clone);
    const size = box.getSize(new Vector3());
    const center = box.getCenter(new Vector3());
    const maxAxis = Math.max(size.x, size.y, size.z) || 1;
    const normalizedScale = (2 / maxAxis) * 1.35;
    const upscale = normalizedScale * 1.51;

    return {
      alignedModel: clone,
      offset: [-center.x, -center.y, -center.z],
      scale: upscale,
    };
  }, [scene]);

  useEffect(() => {
    if (groupRef.current) {
      groupRef.current.rotation.y = (rotationAngle * Math.PI) / 180;
    }
  }, [rotationAngle]);

  return (
    <group ref={groupRef} scale={scale} position={[0, -0.11, 0]}>
      <primitive object={alignedModel} position={offset} />
    </group>
  );
}

useGLTF.preload(CAR_MODEL_URL);

export default function CarScene({ rotationAngle }) {
  return (
    <div className="car-scene">
      <Canvas
        shadows
        camera={{ position: [0, 0.9, 6.4], fov: 32 }}
        gl={{ alpha: true, antialias: true }}
        style={{ background: "transparent" }}
        onCreated={({ gl }) => {
          gl.setClearColor(0x000000, 0);
          gl.toneMapping = ACESFilmicToneMapping;
          gl.outputColorSpace = SRGBColorSpace;
          gl.toneMappingExposure = 1.0;
        }}
      >
        <ambientLight intensity={0.4} />
        <hemisphereLight intensity={0.55} groundColor="#0b0b0b" />
        <directionalLight position={[3, 5, 2]} intensity={1.6} color="#ffffff" />
        <directionalLight
          position={[-4, 3, -2]}
          intensity={0.5}
          color="#dfe5ff"
        />
        <spotLight
          position={[0, 6, 4]}
          angle={0.45}
          penumbra={0.3}
          intensity={0.9}
          color="#ffffff"
        />
        <Suspense fallback={null}>
          <Environment preset="city" background={false} />
          <CarModel rotationAngle={rotationAngle} />
        </Suspense>
        <OrbitControls
          enableZoom={false}
          enablePan={false}
          target={[0, -0.2, 0]}
        />
      </Canvas>
    </div>
  );
}
