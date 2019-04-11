<template>
  <div class="TicTacToe">
    <div class="stat">
      Сыграно игр: {{ games }} | Тёмные поля - исследователи.
    </div>

    <div
      v-for="(agent, agentIndex) in agents"
      :key="agentIndex"
      class="field"
    >
      <div
        v-for="(cell, cellIndex) in agent.field"
        :key="`${agentIndex}:${cellIndex}`"
        :class="['cell', {
          'alive': agent.isAlive,
          'researcher': agentIndex % everyNWillResearcher === 0,
          'victory': agent.isVictory,
        }]"
        @click="setSign(agent, cellIndex)"
      >
        <div v-if="cell !== 0">
          X
        </div>
      </div>
    </div>
  </div>
</template>

<script>
// todo 1 Этап. Научить сеть играть за крестик - выставлять в ряд 3 символа.
// todo 2 Этап. Создание площадки для соревнования сетей. Тренировка 2х сетей играть друг с другом.
// todo 3 Этап. Сохранение весов лучшей предобученной сети для игры с человеком.

import * as tf from '@tensorflow/tfjs';
import { victoryCheckGroups as hasVictory } from './utils';

const agentsCount = 20;
const everyNWillResearcher = 4;
const isAutomatic = true;

let isModelFit = false;

/* eslint-disable no-plusplus */
export default {
  name: 'TicTacToe',

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
      agents: [],
      fieldSize: 9,
      everyNWillResearcher,
      currentStep: 0,
      games: 0,
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
        optimizer: tf.train.adam(0.01),
        loss: 'meanSquaredError',
        metrics: ['accuracy'],
      });
    },

    agentsSetting() {
      for (let i = 0; i < agentsCount; i++) {
        this.agents.push({
          id: i,
          step: 0,
          isAlive: true,
          isVictory: false,
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

      if (this.currentStep > this.fieldSize) {
        isModelFit = true;
      }

      if (isModelFit) {
        await this.modelFit();
      }

      // Замедлялка.
      // await new Promise(resolve => setTimeout(resolve, 1000));
      await this.modelPredict();
    },

    // agent.field - массив символов для отображения: X|O.
    // field - массив значений для обработки, если ячейка не пуста, она равна 1.
    async predict(agent, agentIndex) {
      if (agent.isAlive) {
        let prediction;

        if (agentIndex % everyNWillResearcher === 0) {
          prediction = Math.random();
        } else {
          [prediction] = await this.model.predict(tf.tensor2d([agent.field])).data();
        }

        const cellIndex = this.getCellIndex(prediction);

        if (agent.field[cellIndex] === 0) {
          agent.step += 1;
          agent.field.splice(cellIndex, 1, agent.step / this.fieldSize);

          /* eslint-disable no-confusing-arrow */
          const field = agent.field.map(cell => cell > 0 ? 1 : 0);
          const isWin = hasVictory.horizontalGroup({ field, sign: 1 })
            || hasVictory.verticalGroup({ field, sign: 1, start: 0, step: 2 })
            || hasVictory.obliquelyGroup({ field, sign: 1 });

          if (isWin) {
            agent.isAlive = false;
            agent.isVictory = true;

            this.saveLearning({
              input: agent.field,
              // todo описание! сумма всех значений?
              label: [1],
            });
          } else {
            this.saveLearning({
              input: agent.field,
              // todo описание!
              label: [0.5],
            });
          }
        } else {
          agent.isAlive = false;

          this.saveLearning({
            input: agent.field,
            // todo описание!
            label: [0],
          });
        }
      }
    },

    getCellIndex(prediction) {
      return Math.round(prediction * (this.fieldSize - 1));
    },

    saveLearning({ input, label }) {
      this.learning.inputs.push(input);
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
        step: 0,
        isAlive: true,
        isVictory: false,
        field: [
          0, 0, 0,
          0, 0, 0,
          0, 0, 0,
        ],
      }));

      this.currentStep = 0;
      this.games += 1;
    },

    setSign(agent, cellIndex) {
      if (!isAutomatic && agent.field[cellIndex] === 0) {
        agent.step += 1;
        agent.field.splice(cellIndex, 1, agent.step / this.fieldSize);

        const field = agent.field.map(cell => cell > 0 ? 1 : 0);
        const isWin = hasVictory.horizontalGroup({ field, sign: 1 })
          || hasVictory.verticalGroup({ field, sign: 1, start: 0, step: 2 })
          || hasVictory.obliquelyGroup({ field, sign: 1 });

        console.log('isWin', isWin);
      }
    },
  },
};
</script>

<style scoped>
.TicTacToe {
  display: flex;
  flex-wrap: wrap;
  padding-top: 1.3rem;
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
  --square-size: 4rem;

  margin: 1rem;
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
  background-color: dimgrey;
}

.alive {
  background-color: seagreen;
}

.researcher {
  background-color: #222;
}

.victory {
  background-color: brown;
}
</style>
