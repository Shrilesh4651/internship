<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D HVAC Model</title>
    <style>
        body { margin: 0; }
        canvas { display: block; }
    </style>
</head>
<body>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/dat.gui/0.7.7/dat.gui.min.js"></script>

    <script>
        let scene, camera, renderer;
        let duct, airStream;
        let clock = new THREE.Clock();

        // Simulate WebSocket data (setInterval used for simulation)
        let airflowData = {
            airflowSpeed: 0.5,  // Example airflow speed
            airflowDirection: 'right'  // Example direction
        };

        // Simulate receiving data every 2 seconds
        setInterval(() => {
            airflowData.airflowSpeed = Math.random();  // Simulate changing airflow speed
            airflowData.airflowDirection = Math.random() > 0.5 ? 'left' : 'right';  // Simulate random direction
        }, 2000);

        function init() {
            // Create scene, camera, and renderer
            scene = new THREE.Scene();
            camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            renderer = new THREE.WebGLRenderer();
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.body.appendChild(renderer.domElement);

            // Duct system (basic cube representation)
            const ductGeometry = new THREE.BoxGeometry(5, 0.5, 0.5);
            const ductMaterial = new THREE.MeshLambertMaterial({ color: 0x8b8b8b });
            duct = new THREE.Mesh(ductGeometry, ductMaterial);
            scene.add(duct);

            // Airflow animation (cylinder to represent moving air)
            const airGeometry = new THREE.CylinderGeometry(0.2, 0.2, 5, 32);
            const airMaterial = new THREE.MeshBasicMaterial({ color: 0x00ff00, transparent: true, opacity: 0.5 });
            airStream = new THREE.Mesh(airGeometry, airMaterial);
            airStream.rotation.x = Math.PI / 2; // Position the airflow horizontally
            scene.add(airStream);

            // Lighting
            const light = new THREE.PointLight(0xFFFFFF, 1, 100);
            light.position.set(10, 10, 10);
            scene.add(light);

            camera.position.z = 10;
            animate();
        }

        function animate() {
            const delta = clock.getDelta();
            duct.rotation.y += delta * 0.2;  // Rotate duct for effect

            // Update airflow based on simulated data
            airStream.position.x = airflowData.airflowSpeed * 5;  // Adjust speed
            if (airflowData.airflowDirection === 'left') {
                airStream.rotation.z = Math.PI / 4;
            } else {
                airStream.rotation.z = -Math.PI / 4;
            }

            // Loop animation
            renderer.render(scene, camera);
            requestAnimationFrame(animate);
        }

        // Window resize handling
        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });

        init();
    </script>
</body>
</html>
