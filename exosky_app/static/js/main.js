import * as THREE from 'three';

document.addEventListener('DOMContentLoaded', function() {
    const canvasContainer = document.getElementById('canvasContainer');

    // Basic Three.js setup
    let scene = new THREE.Scene();
    let camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    let renderer = new THREE.WebGLRenderer();

    // Set the size of the renderer and append it to the DOM
    renderer.setSize(window.innerWidth, window.innerHeight);
    canvasContainer.appendChild(renderer.domElement);

    // OrbitControls: allowing zoom and rotation with the mouse
    let controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;  // Damping makes controls smoother
    controls.dampingFactor = 0.05;
    controls.enableZoom = true;
    controls.enablePan = true;

    // Camera initial position
    camera.position.set( 0, 0, 500 ); // Camera starting position
	controls.update();

    // Create an empty geometry to hold stars
    let starGeometry = new THREE.BufferGeometry();
    let starMaterial = new THREE.PointsMaterial({ color: 0xffffff });
    function animate() {
        requestAnimationFrame(animate);
        renderer.render(scene, camera);
    }

    animate();
});


document.getElementById('starTypeSlider').addEventListener('input', function (event) {
    const magnitudeLimit = event.target.value;
    // Fetch stars with the selected magnitude
    // Update stars in the 3D scene...
});

// Navbar Toggle Functionality
let lastScrollTop = 0;
const navbar = document.querySelector('.navbar');

window.addEventListener('scroll', function () {
    let scrollTop = window.pageYOffset || document.documentElement.scrollTop;

    if (scrollTop > lastScrollTop) {
        navbar.classList.add('hidden'); // Hide navbar when scrolling down
    } else {
        navbar.classList.remove('hidden'); // Show navbar when scrolling up
    }

    lastScrollTop = scrollTop <= 0 ? 0 : scrollTop; // Ensure scrollTop doesn't go negative
});
