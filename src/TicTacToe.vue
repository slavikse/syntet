<template>
  <div class="TicTacToe">
    <div class="stat">
      Игр: {{ games }} | Побед: {{ victories }}
    </div>

    <div
      v-for="(agent, agentIndex) in agents"
      :key="agentIndex"
      class="field"
    >
      <div
        v-for="(sign, signIndex) in agent.field"
        :key="`${agentIndex}:${signIndex}`"
        class="cell"
      >
        <div v-if="sign === 1">
          X
        </div>
      </div>
    </div>
  </div>
</template>

<script>
// todo 1 Этап. Обучить сеть играть.
// todo 2 Этап. Создание площадки для соревнования сетей.
// todo 3 Этап. Сохранение весов лучшей предобученной сети для игры с человеком.

import * as tf from '@tensorflow/tfjs';
import { victoryCheckGroups } from './utils';

// todo
let isModelFit = false;

/* eslint-disable no-plusplus */
export default {
  name: 'TicTacToe',

  data() {
    return {
      model: tf.sequential(),
      learning: {
        inputs: [],
        labels: [],
      },
      games: 0,
      victories: 0,
      fieldSize: 9,
      agents: [],
      agentsCount: 5,
      currentStep: 0,
    };
  },

  async mounted() {
    this.setupModel();
    this.agentsSetting();
    await this.modelPredict();
  },

  methods: {
    setupModel() {
      this.model.add(tf.layers.dense({
        inputShape: [9],
        activation: 'sigmoid',
        units: 256,
      }));

      // this.model.add(tf.layers.dropout({
      //   rate: 0.1,
      // }));

      // this.model.add(tf.layers.dense({
      //   activation: 'sigmoid',
      //   units: 128,
      // }));

      this.model.add(tf.layers.dense({
        activation: 'sigmoid',
        units: 1,
      }));

      this.model.compile({
        optimizer: tf.train.adam(0.01),
        loss: 'meanSquaredError',
        metrics: ['accuracy'],
      });
    },

    agentsSetting() {
      for (let i = 0; i < this.agentsCount; i++) {
        this.agents.push({
          id: i,
          field: [
            0, 0, 0,
            0, 0, 0,
            0, 0, 0,
          ],
        });
      }
    },

    async modelPredict() {
      isModelFit = false;

      await Promise.all(this.agents.map(this.predict));
      this.currentStep += 1;

      if (this.currentStep === this.agents.length) {
        isModelFit = true;
      }

      if (isModelFit) {
        await this.modelFit();
      }

      await this.modelPredict();
    },

    // todo getRandomPredict Math.random()
    async predict(agent) {
      const [prediction] = await this.model.predict(tf.tensor2d([agent.field])).data();
      const cellIndex = this.getCellIndex(prediction);

      if (agent.field[cellIndex] === 0) {
        agent.field.splice(cellIndex, 1, 1);

        // sign: 1 - Это крестик (X).
        const label = victoryCheckGroups.horizontalGroup({ cells: agent.field, sign: 1 })
          || victoryCheckGroups.verticalGroup({ cells: agent.field, sign: 1, start: 0, step: 2 })
          || victoryCheckGroups.obliquelyGroup({ cells: agent.field, sign: 1 });

        if (label) {
          this.victories += 1;
          this.saveTraining({ field: agent.field, label: [1] });

          isModelFit = true;
        } else {
          this.saveTraining({ field: agent.field, label: [0.2] });
        }
      } else {
        this.saveTraining({ field: agent.field, label: [0] });
      }
    },

    getCellIndex(prediction) {
      return Math.round(prediction * this.fieldSize);
    },

    saveTraining({ field, label }) {
      this.learning.inputs.push(field);
      this.learning.labels.push(label);
    },

    async modelFit() {
      await this.model.fit(
        tf.tensor2d(this.learning.inputs),
        tf.tensor2d(this.learning.labels),
      );

      this.agentReset();
    },

    agentReset() {
      this.agents = this.agents.map(agent => ({
        id: agent.id,
        field: [
          0, 0, 0,
          0, 0, 0,
          0, 0, 0,
        ],
      }));

      this.games += 1;
      this.currentStep = 0;
    },
  },
};
</script>

<style scoped>
.TicTacToe {
  display: flex;
  flex-wrap: wrap;
  padding-top: 1.5rem;
  user-select: none;
}

.stat {
  position: absolute;
  top: 0;
  left: 1rem;
  color: white;
}

.field {
  --quantity-rows: 3;
  --quantity-columns: 3;
  --square-size: 1.4rem;

  margin: 2px;
  display: grid;
  grid-template-rows: repeat(var(--quantity-rows), var(--square-size));
  grid-template-columns: repeat(var(--quantity-columns), var(--square-size));
  grid-gap: 1px;
}

.cell {
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: seagreen;
}
</style>
