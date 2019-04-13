<template>
  <div
    ref="root"
    class="Bird"
    tabindex="0"
    @keydown.up="agentUp"
  >
    <div class="field">
      <div
        v-for="agent in agents"
        :key="agent.id"
        :style="{ transform: `translate(${agent.x}rem, ${-agent.y}rem)` }"
        :class="['agent', { intersected: agent.isIntersected }]"
      />

      <div
        v-for="wall in walls"
        :key="wall.id"
        :style="{ transform: `translate(${wall.x}rem, ${-wall.y}rem)` }"
        class="wall"
      />
    </div>
  </div>
</template>

<script>
import * as tf from '@tensorflow/tfjs';
import TWEEN from '@tweenjs/tween.js';

let rafId;

const agentState = {
  heightUp: { y: 14 },
  heightDown: { y: 0 },
  flightTime: 400,
  tween: { stop() {} },
};

// 20 - ширина игрового поля. 2 - ширина агента.
const maximumWidthToIntersection = 20 - 2;

export default {
  name: 'Bird',

  data() {
    return {
      model: tf.sequential(),
      // Очищаемые перед следующим поколением накопленные данные агентов для обучения.
      training: {
        inputs: [],
        labels: [],
      },
      // Лучшие агенты в поколении из training набора на которых будет обучаться модель.
      learning: {
        inputs: [],
        labels: [],
      },
      agents: [
        {
          id: `agents_${1}`,
          x: 0,
          y: 4,
          // todo что то с ближайшей преградой?
          //   сейчас одна преграда появляется через равное время.
          width: 2,
          height: 2,
          isIntersected: false,
        },
      ],
      walls: [
        {
          id: `walls_${1}`,
          x: 20,
          y: 0,
          width: 2,
          height: 4,
          movementTime: 1000,
          from: {
            x: 20,
          },
          to: {
            x: -2,
          },
        },
        // {
        //   id: `walls_${2}`,
        //   x: 18 * 1.3,
        //   y: 0,
        //   width: 2,
        //   height: 4,
        //   movementTime: 1000 * 1.3,
        //   from: {
        //     x: 18 * 1.3,
        //   },
        //   to: {
        //     x: -2,
        //   },
        // },
        // {
        //   id: `walls_${3}`,
        //   x: 18 * 1.7,
        //   y: 0,
        //   width: 2,
        //   height: 4,
        //   movementTime: 1000 * 1.7,
        //   from: {
        //     x: 18 * 1.7,
        //   },
        //   to: {
        //     x: -2,
        //   },
        // },
      ],
    };
  },

  async mounted() {
    this.setupModel();
    rafId = requestAnimationFrame(this.gameLoop);

    this.agentSetting();
    this.startWallsMovement();

    await this.modelPredict();
  },

  destroyed() {
    cancelAnimationFrame(rafId);
  },

  methods: {
    setupModel() {
      // y, step.
      this.model.add(tf.layers.dense({
        inputShape: [2],
        activation: 'sigmoid',
        units: 128,
      }));

      // this.model.add(tf.layers.dropout({
      //   rate: 0.1,
      // }));
      //
      // this.model.add(tf.layers.dense({
      //   activation: 'sigmoid',
      //   units: 128,
      // }));

      // jump
      this.model.add(tf.layers.dense({
        activation: 'sigmoid',
        units: 1,
      }));

      this.model.compile({
        optimizer: tf.train.adamax(0.01),
        loss: 'meanSquaredError',
        metrics: ['accuracy'],
      });
    },

    async modelPredict() {
      await Promise.all(this.agents.map(this.predict));

      // await this.modelFit();

      // Замедлялка.
      // await new Promise(resolve => setTimeout(resolve, 1000));
      await this.modelPredict();
    },

    async predict(agent) {
      const [prediction] = await this.model.predict(tf.tensor2d([agent.field])).data();
      console.log('prediction', prediction);
    },

    gameLoop(time) {
      rafId = requestAnimationFrame(this.gameLoop);
      TWEEN.update(time);
    },

    // todo настройка по первому объекту - все одинаковые.
    agentSetting() {
      const [agent] = this.agents;
      const [wall] = this.walls;

      this.$refs.root.style.setProperty('--agent-width', `${agent.width}rem`);
      this.$refs.root.style.setProperty('--agent-height', `${agent.height}rem`);

      this.$refs.root.style.setProperty('--wall-width', `${wall.width}rem`);
      this.$refs.root.style.setProperty('--wall-height', `${wall.height}rem`);
    },

    agentUp() {
      agentState.tween.stop();

      // todo
      const [agent] = this.agents;

      agentState.tween = new TWEEN.Tween(agent)
        .to(agentState.heightUp, agentState.flightTime)
        .easing(TWEEN.Easing.Quadratic.Out)
        .onComplete(this.agentDown)
        .start();
    },

    agentDown() {
      // todo
      const [agent] = this.agents;

      agentState.tween = new TWEEN.Tween(agent)
        .to(agentState.heightDown, agentState.flightTime)
        .easing(TWEEN.Easing.Quadratic.In)
        .onComplete(this.agentFell)
        .start();
    },

    agentFell() {
      console.log('agentFell');
    },

    startWallsMovement() {
      this.walls.forEach(this.runWallMovement);
    },

    runWallMovement(wall) {
      new TWEEN.Tween(wall)
        .to(wall.to, wall.movementTime)
        .onUpdate(() => this.hasWallIntersectionWithAgent(wall))
        .onComplete(() => this.endWallMovement(wall))
        .start();
    },

    // todo
    hasWallIntersectionWithAgent(wall) {
      const [agent] = this.agents;

      const isTopBorderAgent = agent.y + agent.height > wall.y;
      const isRightBorderAgent = agent.x + agent.width > wall.x;
      const isBottomBorderAgent = agent.y < wall.y + wall.height;

      const isDistanceWallFurtherAgent = wall.x > agent.x + agent.width;

      switch (true) {
        case isTopBorderAgent
        && isRightBorderAgent
        && isBottomBorderAgent:
          // todo является окончаем игры агента.
          agent.isIntersected = true;

          // todo del
          setTimeout(() => {
            agent.isIntersected = false;
          }, 1000);
          break;

        case isDistanceWallFurtherAgent:
          console.log('wall', wall.x);
          break;

        default:
      }
    },

    endWallMovement(wall) {
      wall.x = wall.from.x;
      this.runWallMovement(wall);
    },
  },
};
</script>

<style scoped>
.Bird {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  outline: none;

  --agent-width: -1rem;
  --agent-height: -1rem;

  --wall-width: -1rem;
  --wall-height: -1rem;
}

.field {
  position: relative;
  width: 20rem;
  height: 20rem;
  background-color: #222;
  overflow: hidden;
}

/* todo ширина высота из js */
.agent {
  position: absolute;
  bottom: 0;
  width: var(--agent-width);
  height: var(--agent-height);
  background-color: forestgreen;
  will-change: transform;
}

.agent.intersected {
  background-color: yellowgreen;
}

.wall {
  position: absolute;
  bottom: 0;
  width: var(--wall-width);
  height: var(--wall-height);
  background-color: brown;
  will-change: transform;
}
</style>
