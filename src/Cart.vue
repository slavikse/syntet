<template>
  <div class="Cart" />
</template>

<script>
import * as Matter from 'matter-js';

const options = {
  width: 800,
  height: 600,
  pixelRatio: 1,
  background: '#222',
  wireframeBackground: '#111',
  hasBounds: false,
  enabled: true,
  wireframes: true,
  showSleeping: false,
  showDebug: false,
  showBroadphase: false,
  showBounds: false,
  showVelocity: false,
  showCollisions: false,
  showSeparations: false,
  showAxes: false,
  showPositions: false,
  showAngleIndicator: false,
  showIds: false,
  showShadows: false,
  showVertexNumbers: false,
  showConvexHulls: false,
  showInternalEdges: false,
  showMousePosition: false,
};

// https://brm.io/matter-js/docs
export default {
  name: 'Cart',

  mounted() {
    const engine = Matter.Engine.create();
    const render = Matter.Render.create({ element: this.$el, engine, options });

    Matter.Engine.run(engine);
    Matter.Render.run(render);

    const car = Matter.Composites.car(390, 0, 100, 30, 20);
    const ground = Matter.Bodies.rectangle(400, 610, 810, 60, { isStatic: true });

    Matter.World.add(engine.world, [car, ground]);
  },
};
</script>

<style
  lang="scss"
  scoped
>
.Cart {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100vw;
  height: 100vh;
}
</style>
