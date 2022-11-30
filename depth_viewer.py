import base64

import cv2
import numpy as np

_viewer_html = '''
<html>
<head>
    <style>
        body {
            overflow: hidden;
            margin: 0;
        }
    </style>
    <script>
        var image_url = "{{{image_url_marker}}}";
        var depth_url = "{{{depth_url_marker}}}";
        var blah;
        function getImageData( image ) {
            var canvas = document.createElement( 'canvas' );
            canvas.width = image.width;
            canvas.height = image.height;
            var context = canvas.getContext( '2d' );
            context.drawImage( image, 0, 0 );
            return context.getImageData( 0, 0, image.width, image.height );
        }
        window.onload = (e) => {
            var scene = new THREE.Scene();
            scene.background = new THREE.Color( 0xffffff );
            var camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.set(0, 0, 2);
            var renderer = new THREE.WebGLRenderer({
                antialias: true
            });
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.body.appendChild(renderer.domElement);
            var controls = new THREE.OrbitControls(camera, renderer.domElement);
            var reset = document.getElementById('reset')
            reset.addEventListener('click', e => controls.reset())
            function vertexShader() {
                return document.getElementById("vshader").text
            }
            function fragmentShader() {
                return document.getElementById("fshader").text
            }
            var texture = new THREE.TextureLoader().load(image_url, t => {
                var w = t.image.width;
                var h = t.image.height;
                var max = Math.max(w, h);
                var ar = w / h;
                blah = getImageData(t.image);
                console.log('texture:', getImageData(t.image).data)

                var planeGeometry = new THREE.PlaneGeometry(w / max, h / max, w, h);
                var depth = new THREE.TextureLoader().load(depth_url);
                uniforms = {
                    image: { type: "t", value: texture },
                    depth: { type: "t", value: depth },
                    ar: { type: 'f', value: ar }
                }
                let planeMaterial = new THREE.ShaderMaterial({
                    uniforms: uniforms,
                    fragmentShader: fragmentShader(),
                    vertexShader: vertexShader(),
                    side: THREE.DoubleSide
                });
                var points = new THREE.Points(planeGeometry, planeMaterial)
                points.position.set(0, 0, 0)
                scene.add(points)
                render();
            });
            function render() {
                requestAnimationFrame(render);
                renderer.render(scene, camera);
            }
        }
    </script>
</head>
<body>
    <script src="https://threejs.org/build/three.min.js"></script>
    <script src="https://threejs.org/examples/js/controls/OrbitControls.js"></script>
    <script id="vshader" type="x-shader/x-vertex">
        uniform sampler2D depth;
        uniform float ar;
        varying vec3 vUv; 
        vec3 pos;

        void main() {
          vUv = position; 
          pos = position;
          pos.z = texture2D(depth,(vec2(vUv.x,vUv.y*ar)+0.5)).r;

          float s = 2.0 - pos.z;
          pos.x = pos.x * s;
          pos.y = pos.y * s;

          vec4 modelViewPosition = modelViewMatrix * vec4(pos, 1.0);
          gl_Position = projectionMatrix * modelViewPosition; 
          gl_PointSize = 2.0;
        }
    </script>
    <script id="fshader" type="x-shader/x-fragment">
        uniform sampler2D image;
        uniform float ar;
        varying vec3 vUv;

        void main() {
          gl_FragColor = texture2D(image,(vec2(vUv.x,vUv.y*ar)+0.5));
        }
    </script>
    <div style="position:absolute">
        <button id="reset">Reset</button>
    </div>
</body>
</html>
'''

image_url_marker = '{{{image_url_marker}}}'
depth_url_marker = '{{{depth_url_marker}}}'


def depth_viewer2html(image, depth):
    image_rgb = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2RGB)
    _, buffer = cv2.imencode('.jpg', image_rgb)
    image_data_url = 'data:image/jpeg;base64,' + base64.b64encode(buffer).decode('utf-8')
    _, buffer = cv2.imencode('.png', np.array(depth))
    mask_data_url = 'data:image/png;base64,' + base64.b64encode(buffer).decode('utf-8')
    vhtml = str(_viewer_html).replace(image_url_marker, image_data_url).replace(depth_url_marker, mask_data_url)
    e = base64.b64encode(bytes(vhtml, 'utf-8')).decode('utf-8')
    url = f'data:text/html;base64,{e}'
    h = f'<iframe src="{url}" height="600" width="100%"></iframe>'
    return h
