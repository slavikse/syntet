<template>
  <div
    ref="root"
    class="Bird"
    tabindex="0"
    @keydown.up="agentUp(agents[0])"
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

// С учётом размеров агента.
const fieldSize = 18;
// 2 - ширина агента.
const maximumDistanceToIntersection = fieldSize - 2;

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
      // todo хранить saveLearning в агенте, а при обучении брать 5 самых долго живущих.
      // todo добавить параметр долгоживущего. занести его в сеть для обучения?
      agents: [
        {
          id: `agents_${1}`,
          x: 0,
          y: 0,
          width: 2,
          height: 2,
          distance: maximumDistanceToIntersection,
          isIntersected: false,
          heightUp: { y: 18 },
          heightDown: { y: 0 },
          flightTime: 300,
          tween: { stop() {} },
        },
      ],
      walls: [
        {
          id: `walls_${1}`,
          x: 20,
          y: 0,
          width: 2,
          height: 4,
          movementTime: 2000,
          from: {
            x: 20,
          },
          to: {
            x: -2,
          },
          tween: { stop() {} },
        },
        {
          id: `walls_${2}`,
          x: 30,
          y: 16,
          width: 2,
          height: 4,
          movementTime: 3000,
          from: {
            x: 30,
          },
          to: {
            x: -2,
          },
        },
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
    this.agentSetting();
    rafId = requestAnimationFrame(this.gameLoop);

    await this.modelPredict();
    this.restartWallsMovement();

    // window.check = () => {
    //   const [wall] = this.walls;
    //   this.hasWallIntersectionWithAgent(wall);
    // };
  },

  destroyed() {
    cancelAnimationFrame(rafId);
  },

  methods: {
    setupModel() {
      this.model.add(tf.layers.dense({
        inputShape: [2],
        activation: 'sigmoid',
        units: 64,
      }));

      // this.model.add(tf.layers.dropout({
      //   rate: 0.1,
      // }));
      //
      // this.model.add(tf.layers.dense({
      //   activation: 'sigmoid',
      //   units: 128,
      // }));

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

    // todo настройка по первому объекту - все одинаковые.
    agentSetting() {
      const [agent] = this.agents;
      const [wall] = this.walls;

      this.$refs.root.style.setProperty('--agent-width', `${agent.width}rem`);
      this.$refs.root.style.setProperty('--agent-height', `${agent.height}rem`);

      this.$refs.root.style.setProperty('--wall-width', `${wall.width}rem`);
      this.$refs.root.style.setProperty('--wall-height', `${wall.height}rem`);
    },

    gameLoop(time) {
      rafId = requestAnimationFrame(this.gameLoop);
      TWEEN.update(time);
    },

    async modelPredict() {
      await Promise.all(this.agents.map(this.predict));
      // todo вместо цикла, добавить счетчик агентов в строю и сбрасывать после обучения сети.
      const countNotIntersected = this.agents.filter((agent) => !agent.isIntersected).length;

      if (countNotIntersected === 0) {
        this.agentsReset();
        this.stopWallsMovement();
        await this.modelFit();
        this.restartWallsMovement();
      }

      // Замедлялка прогнозирования.
      await new Promise((resolve) => setTimeout(resolve, 500));
      this.modelPredict();
    },

    async predict(agent) {
      if (!agent.isIntersected) {
        const [prediction] = await this.model.predict(tf.tensor2d([
          [
            agent.y / fieldSize,
            agent.distance / fieldSize,
          ],
        ])).data();

        console.log('prediction', prediction);

        if (prediction > 0.5) {
          this.agentUp(agent);
        }
      }
    },

    agentUp(agent) {
      agent.tween.stop();

      agent.tween = new TWEEN.Tween(agent)
        .to(agent.heightUp, agent.flightTime)
        .easing(TWEEN.Easing.Quadratic.Out)
        .onComplete(() => this.agentDown(agent))
        .start();
    },

    agentDown(agent) {
      agent.tween = new TWEEN.Tween(agent)
        .to(agent.heightDown, agent.flightTime)
        .easing(TWEEN.Easing.Quadratic.In)
        .onComplete(() => this.agentFell(agent))
        .start();
    },

    // todo сброс состояния, когда все агенты потерпели неудачу.
    agentFell(agent) {
      console.log('agentFell', agent);
    },

    // todo множественные агенты
    agentsReset() {
      const [agent] = this.agents;

      agent.tween.stop();

      agent.y = 0;
      agent.distance = maximumDistanceToIntersection;
      agent.isIntersected = false;
    },

    stopWallsMovement() {
      this.walls.forEach((wall) => wall.tween.stop());
    },

    restartWallsMovement() {
      this.walls.forEach(this.rerunWallMovement);
    },

    rerunWallMovement(wall) {
      wall.x = wall.from.x;

      wall.tween = new TWEEN.Tween(wall)
        .to(wall.to, wall.movementTime)
        .onUpdate(() => this.hasWallIntersectionWithAgent(wall))
        .onComplete(() => this.rerunWallMovement(wall))
        .start();
    },

    // todo множественные агенты
    hasWallIntersectionWithAgent(wall) {
      const [agent] = this.agents;

      if (!agent.isIntersected) {
        const isTopBorderAgent = agent.y + agent.height > wall.y;
        const isRightBorderAgent = agent.x + agent.width > wall.x;
        const isBottomBorderAgent = agent.y < wall.y + wall.height;

        if (wall.x - agent.width >= 0) {
          const distance = wall.x - agent.width;

          if (distance < agent.distance) {
            agent.distance = distance;
          }
        }

        if (
          isTopBorderAgent
          && isRightBorderAgent
          && isBottomBorderAgent
        ) {
          agent.isIntersected = true;

          // todo сохраняется очень много информации. 60fps.
          this.saveLearning({
            input: [
              agent.y / fieldSize,
              agent.distance / fieldSize,
            ],
            label: [0],
          });
        } else {
          this.saveLearning({
            input: [
              agent.y / fieldSize,
              agent.distance / fieldSize,
            ],
            label: [1],
          });
        }
      }
    },

    // todo training
    saveLearning({ input, label }) {
      // console.log('input', input);
      // console.log('label', label);

      this.learning.inputs.push(input);
      this.learning.labels.push(label);
    },

    // todo training и отбор лучших в поколении?
    async modelFit() {
      await this.model.fit(
        tf.tensor2d(this.learning.inputs),
        tf.tensor2d(this.learning.labels),
      );
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
