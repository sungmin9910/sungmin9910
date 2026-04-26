import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

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
        this.scene.background = new THREE.Color(0x0a0b10); // 심해색 배경
        this.scene.fog = new THREE.Fog(0x0a0b10, 50, 300); // 안개 거리 대폭 확장

        this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        this.camera.position.set(0, 5, 10);

        this.renderer = new THREE.WebGLRenderer({
            canvas: this.canvas,
            antialias: true
        });
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.shadowMap.enabled = true;
        this.renderer.toneMapping = THREE.ReinhardToneMapping;

        // --- Post Processing (AirSim Look) ---
        this.initPostProcessing();

        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;

        // --- 위치 설정 (전북대학교 정문 앞 교차로 - 스트리트 뷰 최적 지점) ---
        this.origin = { lat: 35.84412, lon: 127.12928 }; 
        this.zoom = 18;

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
        // 1. Satellite Map Ground
        this.createSatelliteMap();

        // 2. Clear procedural objects and only add some test obstacles
        this.createScatteredObstacles();
    }

    createSatelliteMap() {
        const tileSize = 400; // 맵 크기 확장
        const loader = new THREE.TextureLoader();
        
        // 1. 위성 지도 로딩 (실패 시를 대비해 여러 서버 시도 또는 세련된 그리드 배경)
        // 전북대학교 공과대학 부근 (Esri 위성 지도)
        // 구글 위성 지도 타일 서버 (가장 확실한 로딩)
        // 전북대 부근 타일 좌표 계산 (Zoom 18)
        const satelliteTexture = loader.load(
            'https://mt1.google.com/vt/lyrs=s&x=222340&y=104975&z=18', 
            undefined, 
            undefined,
            (err) => { console.warn("Google Tiles failed, using fallback."); }
        );
        
        const groundGeo = new THREE.PlaneGeometry(tileSize, tileSize);
        const groundMat = new THREE.MeshStandardMaterial({ 
            map: satelliteTexture,
            color: 0x223344,
            roughness: 0.6,
            metalness: 0.4
        });

        const ground = new THREE.Mesh(groundGeo, groundMat);
        ground.rotation.x = -Math.PI / 2;
        ground.receiveShadow = true;
        ground.name = "ground";
        this.scene.add(ground);

        // 2. 바닥에 세련된 오버레이 그리드 (더 선명하고 미래지향적으로)
        const grid = new THREE.GridHelper(tileSize, 80, 0x00f2ff, 0x111111);
        grid.position.y = 0.1;
        grid.material.opacity = 0.3;
        grid.material.transparent = true;
        this.scene.add(grid);

        // 메인 도로를 시각적으로 강조
        const mainRoad = new THREE.Mesh(
            new THREE.PlaneGeometry(12, tileSize),
            new THREE.MeshStandardMaterial({ color: 0x111111, transparent: true, opacity: 0.6 })
        );
        mainRoad.rotation.x = -Math.PI / 2;
        mainRoad.position.y = 0.05;
        this.scene.add(mainRoad);
    }

    createCampusBuildings() {
        // 위성 지도 위의 주요 건물들을 투명한 박스로 시뮬레이션
        const buildingMat = new THREE.MeshStandardMaterial({ 
            color: 0x222222, 
            transparent: true, 
            opacity: 0.4,
            wireframe: false 
        });

        const boxes = [
            { pos: [-30, 5, -40], size: [20, 10, 40] },
            { pos: [40, 5, 20], size: [30, 15, 20] },
            { pos: [-50, 5, 60], size: [15, 8, 30] }
        ];

        boxes.forEach(b => {
            const mesh = new THREE.Mesh(new THREE.BoxGeometry(...b.size), buildingMat);
            mesh.position.set(...b.pos);
            this.scene.add(mesh);
            this.obstacles.push(mesh);
        });
    }

    createScatteredObstacles() {
        const crateGeo = new THREE.BoxGeometry(2, 2, 2);
        const crateMat = new THREE.MeshStandardMaterial({ color: 0xffa500, emissive: 0xffa500, emissiveIntensity: 0.2 });
        
        for (let i = 0; i < 20; i++) {
            const crate = new THREE.Mesh(crateGeo, crateMat);
            const x = (Math.random() - 0.5) * 200;
            const z = (Math.random() - 0.5) * 200;
            crate.position.set(x, 1, z);
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

    initPostProcessing() {
        this.composer = new EffectComposer(this.renderer);
        
        const renderPass = new RenderPass(this.scene, this.camera);
        this.composer.addPass(renderPass);

        const bloomPass = new UnrealBloomPass(
            new THREE.Vector2(window.innerWidth, window.innerHeight),
            0.6, // intensity (빛 번짐 강도)
            0.5, // radius
            0.8  // threshold
        );
        this.composer.addPass(bloomPass);

        const outputPass = new OutputPass();
        this.composer.addPass(outputPass);
    }
    onWindowResize() {
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        if (this.composer) {
            this.composer.setSize(window.innerWidth, window.innerHeight);
        }
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

                    // --- 로드뷰 동기화 업데이트 ---
                    this.updateRoadView();
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

            // --- 센서 대시보드 가짜 데이터 시뮬레이션 (AirSim 느낌) ---
            this.updateSensorDashboard();
        }

        // --- Render with Post-processing ---
        if (this.composer) {
            this.composer.render();
        } else {
            this.renderer.render(this.scene, this.camera);
        }
    }

    updateRoadView() {
        const lat = this.origin.lat + (this.car.position.z * -0.000009);
        const lon = this.origin.lon + (this.car.position.x * 0.000011);
        
        let heading = (this.car.rotation.y * 180 / Math.PI) % 360;
        if (heading < 0) heading += 360;
        
        const iframe = document.getElementById('street-view-iframe');
        
        if (!this.lastUpdatePos || this.car.position.distanceTo(this.lastUpdatePos) > 3.0) {
            // cbll: 좌표, cbp: 12 (카메라 제어), heading, pitch, zoom 등
            // q 파라미터를 비우고 cbll만 사용하여 스트리트 뷰 강제 호출
            const streetViewUrl = `https://maps.google.com/maps?layer=c&cbll=${lat},${lon}&cbp=12,${heading},0,0,10&source=browser&output=embed`;
            
            iframe.src = streetViewUrl;
            this.lastUpdatePos = this.car.position.clone();
        }
    }

    updateSensorDashboard() {
        // DEPTH 및 SEMANTIC 뷰에 실시간 움직임 효과 (애니메이션 느낌)
        const depth = document.querySelector('.view-content.depth');
        const semantic = document.querySelector('.view-content.semantic');
        const lidar = document.querySelector('.view-content.lidar-mini');
        
        if (depth) depth.style.opacity = 0.5 + Math.random() * 0.5;
        if (semantic) semantic.style.filter = `hue-rotate(${this.car.position.z * 10}deg)`;
    }
}

new Simulator();
