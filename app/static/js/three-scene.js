/* ============================================================
   FORENSIC REPORT ANALYZER — Three.js 3D Scene Engine
   Particle nebula, DNA helix, orbiting spheres, mouse parallax
   ============================================================ */

(function () {
  'use strict';

  // Only run if Three.js is loaded
  if (typeof THREE === 'undefined') {
    console.warn('Three.js not loaded');
    return;
  }

  const CONFIG = {
    particleCount: 2500,
    helixRadius: 3.5,
    helixHeight: 14,
    helixTurns: 4,
    helixPointsPerTurn: 40,
    orbiterCount: 6,
    mouseInfluence: 0.0004,
    cameraZ: 18,
    colors: {
      primary: 0x00e5ff,
      secondary: 0x3d5af1,
      accent: 0xb537f2,
      particle1: 0x00e5ff,
      particle2: 0x3d5af1,
      particle3: 0xb537f2,
      ambient: 0x0a1030,
    },
  };

  let scene, camera, renderer, particles, helix, orbiters;
  let mouseX = 0,
    mouseY = 0;
  let clock;

  function init() {
    const canvas = document.getElementById('three-canvas');
    if (!canvas) return;

    clock = new THREE.Clock();

    // Scene
    scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x020615, 0.035);

    // Camera
    camera = new THREE.PerspectiveCamera(
      60,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    camera.position.set(0, 0, CONFIG.cameraZ);

    // Renderer
    renderer = new THREE.WebGLRenderer({
      canvas: canvas,
      alpha: true,
      antialias: true,
    });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x020615, 1);

    // Lights
    createLights();

    // Objects
    createParticles();
    createDNAHelix();
    createOrbiters();

    // Events
    window.addEventListener('resize', onResize);
    document.addEventListener('mousemove', onMouseMove);

    // Start
    animate();
  }

  function createLights() {
    const ambient = new THREE.AmbientLight(CONFIG.colors.ambient, 0.5);
    scene.add(ambient);

    const pointLight1 = new THREE.PointLight(CONFIG.colors.primary, 1.5, 50);
    pointLight1.position.set(10, 10, 10);
    scene.add(pointLight1);

    const pointLight2 = new THREE.PointLight(CONFIG.colors.accent, 1.2, 50);
    pointLight2.position.set(-10, -5, 8);
    scene.add(pointLight2);

    const pointLight3 = new THREE.PointLight(CONFIG.colors.secondary, 0.8, 40);
    pointLight3.position.set(0, -10, 5);
    scene.add(pointLight3);
  }

  function createParticles() {
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(CONFIG.particleCount * 3);
    const colors = new Float32Array(CONFIG.particleCount * 3);
    const sizes = new Float32Array(CONFIG.particleCount);

    const colorChoices = [
      new THREE.Color(CONFIG.colors.particle1),
      new THREE.Color(CONFIG.colors.particle2),
      new THREE.Color(CONFIG.colors.particle3),
    ];

    for (let i = 0; i < CONFIG.particleCount; i++) {
      const i3 = i * 3;

      // Spread particles in a sphere
      const radius = 15 + Math.random() * 25;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);

      positions[i3] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      positions[i3 + 2] = radius * Math.cos(phi);

      const color = colorChoices[Math.floor(Math.random() * colorChoices.length)];
      colors[i3] = color.r;
      colors[i3 + 1] = color.g;
      colors[i3 + 2] = color.b;

      sizes[i] = Math.random() * 2 + 0.5;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

    const material = new THREE.PointsMaterial({
      size: 0.12,
      vertexColors: true,
      transparent: true,
      opacity: 0.7,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      sizeAttenuation: true,
    });

    particles = new THREE.Points(geometry, material);
    scene.add(particles);
  }

  function createDNAHelix() {
    helix = new THREE.Group();

    const { helixRadius, helixHeight, helixTurns, helixPointsPerTurn } = CONFIG;
    const totalPoints = helixTurns * helixPointsPerTurn;

    // Strand material
    const strandMaterial = new THREE.MeshPhongMaterial({
      color: CONFIG.colors.primary,
      emissive: CONFIG.colors.primary,
      emissiveIntensity: 0.3,
      transparent: true,
      opacity: 0.8,
      shininess: 100,
    });

    const strandMaterial2 = new THREE.MeshPhongMaterial({
      color: CONFIG.colors.accent,
      emissive: CONFIG.colors.accent,
      emissiveIntensity: 0.3,
      transparent: true,
      opacity: 0.8,
      shininess: 100,
    });

    // Create helix strands using spheres along the path
    for (let i = 0; i < totalPoints; i++) {
      const t = i / totalPoints;
      const angle = t * Math.PI * 2 * helixTurns;
      const y = t * helixHeight - helixHeight / 2;

      // Strand 1
      const x1 = Math.cos(angle) * helixRadius;
      const z1 = Math.sin(angle) * helixRadius;

      const sphere1 = new THREE.Mesh(
        new THREE.SphereGeometry(0.12, 8, 8),
        strandMaterial
      );
      sphere1.position.set(x1, y, z1);
      helix.add(sphere1);

      // Strand 2 (opposite)
      const x2 = Math.cos(angle + Math.PI) * helixRadius;
      const z2 = Math.sin(angle + Math.PI) * helixRadius;

      const sphere2 = new THREE.Mesh(
        new THREE.SphereGeometry(0.12, 8, 8),
        strandMaterial2
      );
      sphere2.position.set(x2, y, z2);
      helix.add(sphere2);

      // Cross-bars (every few points)
      if (i % 4 === 0) {
        const barMaterial = new THREE.MeshPhongMaterial({
          color: CONFIG.colors.secondary,
          emissive: CONFIG.colors.secondary,
          emissiveIntensity: 0.2,
          transparent: true,
          opacity: 0.5,
        });

        const barGeometry = new THREE.CylinderGeometry(0.04, 0.04, helixRadius * 2, 6);
        const bar = new THREE.Mesh(barGeometry, barMaterial);

        bar.position.set((x1 + x2) / 2, y, (z1 + z2) / 2);
        bar.rotation.z = Math.atan2(z2 - z1, x2 - x1);
        bar.rotation.x = Math.PI / 2;

        // Rotate bar to connect the two points
        const direction = new THREE.Vector3(x2 - x1, 0, z2 - z1).normalize();
        const axis = new THREE.Vector3(0, 1, 0);
        const quaternion = new THREE.Quaternion().setFromUnitVectors(axis, direction);
        bar.setRotationFromQuaternion(quaternion);

        helix.add(bar);
      }
    }

    helix.position.set(8, 0, -5);
    helix.rotation.z = 0.3;
    scene.add(helix);
  }

  function createOrbiters() {
    orbiters = [];

    for (let i = 0; i < CONFIG.orbiterCount; i++) {
      const size = 0.2 + Math.random() * 0.3;
      const color =
        i % 3 === 0
          ? CONFIG.colors.primary
          : i % 3 === 1
          ? CONFIG.colors.secondary
          : CONFIG.colors.accent;

      const geometry = new THREE.SphereGeometry(size, 16, 16);
      const material = new THREE.MeshPhongMaterial({
        color: color,
        emissive: color,
        emissiveIntensity: 0.6,
        transparent: true,
        opacity: 0.85,
      });

      const mesh = new THREE.Mesh(geometry, material);

      // Glow shell
      const glowGeometry = new THREE.SphereGeometry(size * 2.5, 16, 16);
      const glowMaterial = new THREE.MeshBasicMaterial({
        color: color,
        transparent: true,
        opacity: 0.08,
        blending: THREE.AdditiveBlending,
      });
      const glow = new THREE.Mesh(glowGeometry, glowMaterial);
      mesh.add(glow);

      const orbiter = {
        mesh: mesh,
        radius: 6 + Math.random() * 8,
        speed: 0.15 + Math.random() * 0.3,
        offset: Math.random() * Math.PI * 2,
        yAmplitude: 2 + Math.random() * 4,
        ySpeed: 0.2 + Math.random() * 0.3,
      };

      scene.add(mesh);
      orbiters.push(orbiter);
    }
  }

  function onResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  }

  function onMouseMove(event) {
    mouseX = (event.clientX - window.innerWidth / 2) * CONFIG.mouseInfluence;
    mouseY = (event.clientY - window.innerHeight / 2) * CONFIG.mouseInfluence;
  }

  function animate() {
    requestAnimationFrame(animate);

    const elapsed = clock.getElapsedTime();

    // Camera follow mouse
    camera.position.x += (mouseX * 8 - camera.position.x) * 0.02;
    camera.position.y += (-mouseY * 8 - camera.position.y) * 0.02;
    camera.lookAt(scene.position);

    // Rotate particles
    if (particles) {
      particles.rotation.y += 0.0005;
      particles.rotation.x += 0.0002;
    }

    // Rotate DNA helix
    if (helix) {
      helix.rotation.y += 0.008;
      helix.position.y = Math.sin(elapsed * 0.3) * 0.5;
    }

    // Animate orbiters
    if (orbiters) {
      orbiters.forEach((o) => {
        const t = elapsed * o.speed + o.offset;
        o.mesh.position.x = Math.cos(t) * o.radius;
        o.mesh.position.z = Math.sin(t) * o.radius;
        o.mesh.position.y = Math.sin(elapsed * o.ySpeed + o.offset) * o.yAmplitude;
      });
    }

    renderer.render(scene, camera);
  }

  // Auto-init when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
