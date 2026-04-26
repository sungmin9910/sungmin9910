import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// --- LiDAR 클래스 ---
class LidarSensor {
    constructor(scene, car) {
        this.scene = scene;
        this.car = car;
        this.raycaster = new THREE.Raycaster();
        this.beams = [];
        this.points = new THREE.Points(
            new THREE.BufferGeometry(),
            new THREE.PointsMaterial({ color: 0xff0000, size: 0.1 })
        );
        this.scene.add(this.points);

        // 시각적 빔 라인
        this.lineMaterial = new THREE.LineBasicMaterial({ color: 0x00f2ff, transparent: true, opacity: 0.2 });
        this.lineGeometry = new THREE.BufferGeometry();
        this.lines = new THREE.LineSegments(this.lineGeometry, this.lineMaterial);
        this.scene.add(this.lines);
    }

    update(obstacles) {
        const beamCount = 32;
        const range = 15;
        const hitPositions = [];
        const linePositions = [];

        for (let i = 0; i < beamCount; i++) {
            const angle = (i / beamCount) * Math.PI * 2;
            const direction = new THREE.Vector3(Math.sin(angle), 0, Math.cos(angle));
            
            this.raycaster.set(this.car.position.clone().add(new THREE.Vector3(0, 0.5, 0)), direction);
            const intersects = this.raycaster.intersectObjects(obstacles);

            if (intersects.length > 0 && intersects[0].distance < range) {
                const hitPoint = intersects[0].point;
                hitPositions.push(hitPoint.x, hitPoint.y, hitPoint.z);
                
                linePositions.push(this.car.position.x, this.car.position.y + 0.5, this.car.position.z);
                linePositions.push(hitPoint.x, hitPoint.y, hitPoint.z);
            } else {
                const endPoint = this.car.position.clone().add(direction.multiplyScalar(range));
                linePositions.push(this.car.position.x, this.car.position.y + 0.5, this.car.position.z);
                linePositions.push(endPoint.x, endPoint.y + 0.5, endPoint.z);
            }
        }

        this.points.geometry.setAttribute('position', new THREE.Float32BufferAttribute(hitPositions, 3));
        this.lineGeometry.setAttribute('position', new THREE.Float32BufferAttribute(linePositions, 3));
    }
}

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

        // --- 자율주행 상태 변수 ---
        this.target = null;
        this.obstacles = [];
        this.isAutonomous = false;

        this.initLights();
        this.initWorld();
        this.initCar();
        this.initTargetMarker();
        
        // LiDAR 초기화
        this.lidar = new LidarSensor(this.scene, this.car);

        this.animate();

        window.addEventListener('resize', () => this.onWindowResize());
        window.addEventListener('mousedown', (e) => this.onMouseDown(e));
    }

    initTargetMarker() {
        const geo = new THREE.RingGeometry(0.8, 1, 32);
        const mat = new THREE.MeshBasicMaterial({ color: 0x00f2ff, side: THREE.DoubleSide });
        this.targetMarker = new THREE.Mesh(geo, mat);
        this.targetMarker.rotation.x = -Math.PI / 2;
        this.targetMarker.visible = false;
        this.scene.add(this.targetMarker);

        const glowGeo = new THREE.CylinderGeometry(0.1, 0.1, 10, 32);
        const glowMat = new THREE.MeshBasicMaterial({ color: 0x00f2ff, transparent: true, opacity: 0.3 });
        const glow = new THREE.Mesh(glowGeo, glowMat);
        glow.position.y = 5;
        this.targetMarker.add(glow);
    }

    onMouseDown(event) {
        // 클릭으로 목표 지점 설정
        const mouse = new THREE.Vector2(
            (event.clientX / window.innerWidth) * 2 - 1,
            -(event.clientY / window.innerHeight) * 2 + 1
        );

        const raycaster = new THREE.Raycaster();
        raycaster.setFromCamera(mouse, this.camera);
        const intersects = raycaster.intersectObject(this.scene.getObjectByName("ground"));

        if (intersects.length > 0) {
            this.target = intersects[0].point;
            this.targetMarker.position.copy(this.target);
            this.targetMarker.position.y = 0.05;
            this.targetMarker.visible = true;
            this.isAutonomous = true;
            document.getElementById('status-val').innerText = "AUTONOMOUS";
            document.getElementById('status-val').classList.add('active');
        }
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
        // 1. Ground - Large Warehouse Floor
        const groundGeo = new THREE.PlaneGeometry(500, 500);
        const groundMat = new THREE.MeshStandardMaterial({ 
            color: 0x080808,
            roughness: 0.9,
            metalness: 0.1
        });
        const ground = new THREE.Mesh(groundGeo, groundMat);
        ground.rotation.x = -Math.PI / 2;
        ground.receiveShadow = true;
        ground.name = "ground";
        this.scene.add(ground);

        // 2. Complex Road System (Crossroads & Loops)
        this.createComplexRoads();

        // 3. Dense Warehouse Buildings
        this.createDenseBuildings();

        // 4. Random Obstacles (Crates, Barriers)
        this.createScatteredObstacles();
    }

    createComplexRoads() {
        // Main Grid Road System
        const roadMat = new THREE.MeshStandardMaterial({ color: 0x151515 });
        
        // Vertical Roads
        const vRoads = [-50, 0, 50];
        vRoads.forEach(x => {
            const road = new THREE.Mesh(new THREE.PlaneGeometry(12, 300), roadMat);
            road.rotation.x = -Math.PI / 2;
            road.position.set(x, 0.01, 0);
            this.scene.add(road);
        });

        // Horizontal Roads
        const hRoads = [-50, 0, 50];
        hRoads.forEach(z => {
            const road = new THREE.Mesh(new THREE.PlaneGeometry(300, 12), roadMat);
            road.rotation.x = -Math.PI / 2;
            road.position.set(0, 0.01, z);
            this.scene.add(road);
        });
    }

    createDenseBuildings() {
        const boxMat = new THREE.MeshStandardMaterial({ color: 0x1a1a1a });
        const positions = [
            [-25, 5, -25], [25, 5, -25], [-25, 5, 25], [25, 5, 25],
            [-75, 8, 0], [75, 8, 0], [0, 8, -75], [0, 8, 75]
        ];

        positions.forEach(pos => {
            const size = Math.random() * 10 + 10;
            const height = Math.random() * 15 + 5;
            const building = new THREE.Mesh(new THREE.BoxGeometry(size, height, size), boxMat);
            building.position.set(pos[0], height/2, pos[2]);
            building.castShadow = true;
            this.scene.add(building);
            this.obstacles.push(building);

            // Detail lights
            const lightGeo = new THREE.PlaneGeometry(1, 4);
            const lightMat = new THREE.MeshStandardMaterial({ color: 0x00f2ff, emissive: 0x00f2ff, emissiveIntensity: 5 });
            const lightStrip = new THREE.Mesh(lightGeo, lightMat);
            lightStrip.position.set(pos[0], height/2, pos[2] + size/2 + 0.1);
            this.scene.add(lightStrip);
        });
    }

    createScatteredObstacles() {
        const crateGeo = new THREE.BoxGeometry(2, 2, 2);
        const crateMat = new THREE.MeshStandardMaterial({ color: 0x8b4513 });
        
        // Randomly place obstacles on roads to test avoidance
        for (let i = 0; i < 40; i++) {
            const crate = new THREE.Mesh(crateGeo, crateMat);
            // Place some on roads
            const x = (Math.random() - 0.5) * 150;
            const z = (Math.random() - 0.5) * 150;
            crate.position.set(x, 1, z);
            crate.rotation.y = Math.random() * Math.PI;
            this.scene.add(crate);
            this.obstacles.push(crate);
        }
    }

    initCar() {
        // Car setup (Keeping it simple but centered on road)
        const carGroup = new THREE.Group();

        // Body (More Cyberpunk-ish)
        const bodyGeo = new THREE.BoxGeometry(2, 0.5, 4);
        const bodyMat = new THREE.MeshStandardMaterial({ color: 0x00f2ff, metalness: 0.8, roughness: 0.2 });
        const body = new THREE.Mesh(bodyGeo, bodyMat);
        body.position.y = 0.6;
        body.castShadow = true;
        carGroup.add(body);

        // Underglow Light
        const light = new THREE.PointLight(0x00f2ff, 2, 5);
        light.position.set(0, 0.1, 0);
        carGroup.add(light);

        // Cockpit
        const cockGeo = new THREE.BoxGeometry(1.4, 0.4, 2);
        const cockMat = new THREE.MeshStandardMaterial({ color: 0x111111, transparent: true, opacity: 0.8 });
        const cockpit = new THREE.Mesh(cockGeo, cockMat);
        cockpit.position.set(0, 1.0, -0.2);
        carGroup.add(cockpit);

        // Wheels
        const wheelGeo = new THREE.CylinderGeometry(0.4, 0.4, 0.4, 32);
        const wheelMat = new THREE.MeshStandardMaterial({ color: 0x111111 });
        
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
        this.car.position.x = 2; // Start on right lane
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
        
        // LiDAR 데이터 업데이트
        this.lidar.update(this.obstacles);

        if (this.car) {
            if (this.isAutonomous && this.target) {
                const pos = this.car.position;
                const dist = pos.distanceTo(this.target);

                if (dist > 1.0) {
                    // 1. 목표 지점 방향 계산 (Attractive Force)
                    const targetDir = new THREE.Vector3().subVectors(this.target, pos).normalize();
                    
                    // 2. 장애물 회피 방향 계산 (Repulsive Force)
                    const avoidanceDir = new THREE.Vector3(0, 0, 0);
                    const beamCount = 32;
                    const ray = new THREE.Raycaster();
                    const range = 10;

                    for (let i = 0; i < beamCount; i++) {
                        const angle = (i / beamCount) * Math.PI * 2;
                        const direction = new THREE.Vector3(Math.sin(angle), 0, Math.cos(angle));
                        
                        ray.set(pos.clone().add(new THREE.Vector3(0, 0.5, 0)), direction);
                        const intersects = ray.intersectObjects(this.obstacles);

                        if (intersects.length > 0 && intersects[0].distance < range) {
                            // 장애물이 가까울수록 더 강한 반발력
                            const force = (range - intersects[0].distance) / range;
                            avoidanceDir.add(direction.clone().multiplyScalar(-force * 2.0));
                        }
                    }

                    // 3. 최종 방향 계산 (목표 + 회피)
                    const finalDir = new THREE.Vector3().addVectors(targetDir, avoidanceDir).normalize();
                    
                    // 4. 조향 (현재 방향에서 최종 방향으로 부드럽게 회전)
                    const currentDir = new THREE.Vector3(0, 0, -1).applyQuaternion(this.car.quaternion);
                    const angle = currentDir.angleTo(finalDir);
                    
                    if (angle > 0.05) {
                        const cross = new THREE.Vector3().crossVectors(currentDir, finalDir);
                        const steerDir = cross.y > 0 ? 1 : -1;
                        this.car.rotation.y += 0.05 * steerDir;
                    }

                    // 5. 전진 (주변 장애물이 많으면 감속)
                    const obstaclePenalty = avoidanceDir.length();
                    const speed = Math.max(0.02, Math.min(0.15, dist * 0.05) * (1 - obstaclePenalty * 0.5));
                    this.car.translateZ(-speed);
                    
                    document.getElementById('speed-val').innerText = (speed * 500).toFixed(0);
                } else {
                    this.isAutonomous = false;
                    this.targetMarker.visible = false;
                    document.getElementById('status-val').innerText = "ARRIVED";
                    document.getElementById('speed-val').innerText = "0";
                }
            }
            
            // Camera follow (Smooth)
            const targetCamPos = new THREE.Vector3().copy(this.car.position);
            const offset = new THREE.Vector3(0, 4, 8).applyQuaternion(this.car.quaternion);
            targetCamPos.add(offset);
            
            this.camera.position.lerp(targetCamPos, 0.1);
            this.camera.lookAt(this.car.position.clone().add(new THREE.Vector3(0, 1, 0)));

            // Update UI
            document.getElementById('pos-x').innerText = this.car.position.x.toFixed(1);
            document.getElementById('pos-z').innerText = this.car.position.z.toFixed(1);
        }

        this.renderer.render(this.scene, this.camera);
    }
}

new Simulator();
