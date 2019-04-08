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
        v-for="(cell, cellIndex) in agent.field"
        :key="`${agentIndex}:${cellIndex}`"
        :class="[
          'cell',
          { 'researcher': (agentIndex + 1) % (everyNWillResearcher + 1) === 0 }
        ]"
        @click="setSign(agent, cellIndex)"
      >
        {{ cell }}
      </div>
    </div>
  </div>
</template>

<script>
// todo 2 Этап. Создание площадки для соревнования сетей.
// todo 3 Этап. Сохранение весов лучшей предобученной сети для игры с человеком.

import * as tf from '@tensorflow/tfjs';
import { victoryCheckGroups } from './utils';

const isAutomatic = true;

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

      agents: [],
      agentsCount: 50,
      // Игровое поле: agents.length - 1
      fieldSize: 9 - 1,
      currentStep: 0,

      everyNWillResearcherCounter: 0,
      everyNWillResearcher: 9,

      games: 0,
      victories: 0,

      isModelFit: false,
    };
  },

  async mounted() {
    this.setupModel();
    this.agentsSetting();

    if (isAutomatic) {
      await this.modelPredict();
    }
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
          // X | O
          sign: 'X',
          field: [
            '', '', '',
            '', '', '',
            '', '', '',
          ],
        });
      }
    },

    async modelPredict() {
      this.isModelFit = false;

      await Promise.all(this.agents.map(this.predict));
      this.currentStep += 1;

      if (this.currentStep === this.fieldSize + 1) {
        this.isModelFit = true;
      }

      if (this.isModelFit) {
        await this.modelFit();
      }

      // Замедлялка.
      // await new Promise(resolve => setTimeout(resolve, 100));
      await this.modelPredict();
    },

    // agent.field - массив символов для отображения: X|O.
    // field - массив значений для обработки, если ячейка не пуста, она равна 1.
    async predict(agent) {
      const field = agent.field.map(cell => cell.length);
      let prediction;

      if (this.everyNWillResearcherCounter === this.everyNWillResearcher) {
        this.everyNWillResearcherCounter = 0;
        prediction = Math.random();
      } else {
        this.everyNWillResearcherCounter += 1;
        [prediction] = await this.model.predict(tf.tensor2d([field])).data();
      }

      const cellIndex = this.getCellIndex(prediction);
      const { sign } = agent;

      if (agent.field[cellIndex].length === 0) {
        agent.field.splice(cellIndex, 1, sign);

        const label = victoryCheckGroups.horizontalGroup({ field: agent.field, sign })
          || victoryCheckGroups.verticalGroup({ field: agent.field, sign, start: 0, step: 2 })
          || victoryCheckGroups.obliquelyGroup({ field: agent.field, sign });

        if (label) {
          this.victories += 1;
          this.isModelFit = true;
          this.saveLearning({ field, label: [1] });
        } else {
          this.saveLearning({ field, label: [0.3] });
        }
      } else {
        this.saveLearning({ field, label: [0] });
      }

      this.swapSign(agent);
    },

    getCellIndex(prediction) {
      return Math.round(prediction * this.fieldSize);
    },

    swapSign(agent) {
      if (agent.sign === 'X') {
        agent.sign = 'O';
      } else {
        agent.sign = 'X';
      }
    },

    saveLearning({ field, label }) {
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
        // X | O
        sign: 'X',
        field: [
          '', '', '',
          '', '', '',
          '', '', '',
        ],
      }));

      this.everyNWillResearcherCounter = 0;
      this.currentStep = 0;
      this.games += 1;
    },

    setSign(agent, cellIndex) {
      if (!isAutomatic) {
        agent.field.splice(cellIndex, 1, agent.sign);
        const { field, sign } = agent;

        const label = victoryCheckGroups.horizontalGroup({ field, sign })
          || victoryCheckGroups.verticalGroup({ field, sign, start: 0, step: 2 })
          || victoryCheckGroups.obliquelyGroup({ field, sign });

        console.log('sign / label', sign, label);

        this.swapSign(agent);
      }
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
  --square-size: 2rem;

  margin: 5px;
  display: grid;
  grid-template-rows: repeat(var(--quantity-rows), var(--square-size));
  grid-template-columns: repeat(var(--quantity-columns), var(--square-size));
  grid-gap: 1px;
}

.cell {
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 1.5rem;
  background-color: seagreen;
}

.researcher {
  background-color: yellowgreen;
}
</style>
