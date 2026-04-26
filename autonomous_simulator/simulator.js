import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

class Simulator {
    constructor() {
        this.container = document.getElementById('app');
        this.canvas = document.getElementById('sim-canvas');
        
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x050505);
        this.scene.fog = new THREE.Fog(0x050505, 10, 50);

        this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        this.camera.position.set(0, 5, 10);

        this.renderer = new THREE.WebGLRenderer({
            canvas: this.canvas,
            antialias: true
        });
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.shadowMap.enabled = true;

        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;

        this.initLights();
        this.initWorld();
        this.initCar();
        this.animate();

        window.addEventListener('resize', () => this.onWindowResize());
    }

    initLights() {
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
        this.scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0x00f2ff, 1);
        dirLight.position.set(10, 20, 10);
        dirLight.castShadow = true;
        this.scene.add(dirLight);

        const pointLight = new THREE.PointLight(0xffffff, 1);
        pointLight.position.set(-10, 10, -10);
        this.scene.add(pointLight);
    }

    initWorld() {
        // Grid Floor
        const grid = new THREE.GridHelper(100, 50, 0x00f2ff, 0x222222);
        this.scene.add(grid);

        // Ground Plane
        const groundGeo = new THREE.PlaneGeometry(100, 100);
        const groundMat = new THREE.MeshStandardMaterial({ 
            color: 0x111111,
            roughness: 0.8,
            metalness: 0.2
        });
        const ground = new THREE.Mesh(groundGeo, groundMat);
        ground.rotation.x = -Math.PI / 2;
        ground.receiveShadow = true;
        this.scene.add(ground);
    }

    initCar() {
        // Simple Car Placeholder
        const carGroup = new THREE.Group();

        // Body
        const bodyGeo = new THREE.BoxGeometry(2, 0.6, 4);
        const bodyMat = new THREE.MeshStandardMaterial({ color: 0x00f2ff });
        const body = new THREE.Mesh(bodyGeo, bodyMat);
        body.position.y = 0.5;
        body.castShadow = true;
        carGroup.add(body);

        // Cockpit
        const cockGeo = new THREE.BoxGeometry(1.4, 0.5, 1.5);
        const cockMat = new THREE.MeshStandardMaterial({ color: 0x111111 });
        const cockpit = new THREE.Mesh(cockGeo, cockMat);
        cockpit.position.set(0, 1, 0);
        carGroup.add(cockpit);

        // Wheels
        const wheelGeo = new THREE.CylinderGeometry(0.4, 0.4, 0.4, 16);
        const wheelMat = new THREE.MeshStandardMaterial({ color: 0x222222 });
        
        const wheelPos = [
            [-1.1, 0.4, 1.3], [1.1, 0.4, 1.3],
            [-1.1, 0.4, -1.3], [1.1, 0.4, -1.3]
        ];

        wheelPos.forEach(pos => {
            const wheel = new THREE.Mesh(wheelGeo, wheelMat);
            wheel.rotation.z = Math.PI / 2;
            wheel.position.set(...pos);
            carGroup.add(wheel);
        });

        this.car = carGroup;
        this.scene.add(this.car);
    }

    onWindowResize() {
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        this.controls.update();
        
        // Basic animation to show life
        if (this.car) {
            this.car.position.z -= 0.01;
            if (this.car.position.z < -20) this.car.position.z = 20;
            
            // Update UI
            document.getElementById('pos-z').innerText = this.car.position.z.toFixed(2);
            document.getElementById('speed-val').innerText = "30";
        }

        this.renderer.render(this.scene, this.camera);
    }
}

new Simulator();
