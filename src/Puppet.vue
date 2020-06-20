<template>
  <div class="Puppet" />
</template>

<script>
import * as Matter from 'matter-js';

// const { clientHeight, clientWidth } = document.documentElement;

export default {
  name: 'Puppet',

  mounted() {
    this.doublePendulum();

    // const engine = Engine.create();
    //
    // const render = Render.create({ element: this.$el, engine });
    //
    // const boxA = Bodies.rectangle(400, 200, 80, 80);
    // const boxB = Bodies.rectangle(450, 50, 80, 80);
    // const ground = Bodies.rectangle(400, 610, 810, 60, { isStatic: true });
    //
    // World.add(engine.world, [boxA, boxB, ground]);
    //
    // Engine.run(engine);
    //
    // Render.run(render);
  },

  methods: {
    /* eslint-disable */
    doublePendulum() {
      var Engine = Matter.Engine,
        Events = Matter.Events,
        Render = Matter.Render,
        Runner = Matter.Runner,
        Body = Matter.Body,
        Composite = Matter.Composite,
        Composites = Matter.Composites,
        Constraint = Matter.Constraint,
        MouseConstraint = Matter.MouseConstraint,
        Mouse = Matter.Mouse,
        World = Matter.World,
        Bodies = Matter.Bodies,
        Vector = Matter.Vector;

      // create engine
      var engine = Engine.create(),
        world = engine.world;

      // create renderer
      var render = Render.create({
        element: this.$el,
        engine,
        options: {
          width: 800,
          height: 600,
          wireframes: false,
          background: '#0f0f13',
        },
      });

      Render.run(render);

      var runner = Runner.create();
      Runner.run(runner, engine);

      var group = Body.nextGroup(true),
        length = 100,
        width = 10;

      var pendulum = Composites.stack(350, 160, 2, 1, -20, 0, function (x, y) {
        return Bodies.rectangle(x, y, length, width, {
          collisionFilter: { group: group },
          frictionAir: 0,
          chamfer: 5,
          render: {
            fillStyle: 'transparent',
            lineWidth: 1,
          },
        });
      });

      pendulum.bodies[0].render.strokeStyle = '#4a485b';
      pendulum.bodies[1].render.strokeStyle = '#4a485b';

      world.gravity.scale = 0.01;

      Composites.chain(pendulum, 0.45, 0, -0.45, 0, {
        stiffness: 0.9,
        length: 0,
        angularStiffness: 0.7,
        render: {
          strokeStyle: '#4a485b',
        },
      });

      Composite.add(pendulum, Constraint.create({
        bodyB: pendulum.bodies[0],
        pointB: { x: -length * 0.42, y: 0 },
        pointA: { x: pendulum.bodies[0].position.x - length * 0.42, y: pendulum.bodies[0].position.y },
        stiffness: 0.9,
        length: 0,
        render: {
          strokeStyle: '#4a485b',
        },
      }));

      var lowerArm = pendulum.bodies[1];

      Body.rotate(lowerArm, -Math.PI * 0.3, {
        x: lowerArm.position.x - 100,
        y: lowerArm.position.y,
      });

      World.add(world, pendulum);

      var mouse = Mouse.create(render.canvas),
        mouseConstraint = MouseConstraint.create(engine, {
          mouse,
          constraint: {
            stiffness: 0.2,
            render: {
              visible: false,
            },
          },
        });

      World.add(world, mouseConstraint);

      render.mouse = mouse;

      // Render.lookAt(render, {
      //   min: { x: 0, y: 0 },
      //   max: { x: 700, y: 600 },
      // });

      return {
        engine,
        runner,
        render,
        canvas: render.canvas,
        stop() {
          Matter.Render.stop(render);
          Matter.Runner.stop(runner);
        },
      };
    },
  },
};
</script>

<style
  lang="scss"
  scoped
>
.Puppet {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100vw;
  height: 100vh;
}
</style>
