<template>
  <div class="TicTacToe">
    <div class="stat">
      Игр: {{ games }} | Побед: {{ victories }}
    </div>

    <div class="field">
      <div
        v-for="(sign, index) in field"
        :key="index"
        class="cell"
        @click="fill(index)"
      >
        <div
          v-if="sign === 1"
          class="agent"
        >
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

export default {
  name: 'TicTacToe',

  data() {
    return {
      model: tf.sequential(),
      // Лучшие агенты в поколении из training набора на которых будет обучаться модель.
      learning: {
        inputs: [],
        labels: [],
      },
      games: 0,
      victories: 0,
      agent: {
        id: 1,
        style: undefined,
      },

      madeMoves: 0,
      field: [
        0, 0, 0,
        0, 0, 0,
        0, 0, 0,
      ],
      fieldSize: -1,
    };
  },

  async mounted() {
    this.setupModel();
    this.fieldSetting();

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

    fieldSetting() {
      this.fieldSize = this.field.length;
    },

    async modelPredict() {
      let isVictories = false;

      const prediction = await this.model.predict(tf.tensor2d([this.field])).data();
      const cellIndex = this.getCellIndex(prediction);

      if (this.field[cellIndex] === 0) {
        this.fill(cellIndex);

        // sign: 1 - Это крестик. X.
        const label = victoryCheckGroups.horizontalGroup({ cells: this.field, sign: 1 })
          || victoryCheckGroups.verticalGroup({ cells: this.field, sign: 1, start: 0, step: 2 })
          || victoryCheckGroups.obliquelyGroup({ cells: this.field, sign: 1 });

        if (label) {
          isVictories = true;
          this.victories += 1;
          this.saveTraining({ label: 1 });
          await this.modelFit();
        } else {
          // todo 0.5 ???
          this.saveTraining({ label: 0.5 });
        }
      } else {
        this.saveTraining({ label: 0 });
      }

      if (!isVictories) {
        this.madeMoves += 1;

        if (this.madeMoves === this.fieldSize) {
          await this.modelFit();
        }
      }

      // Замедление прогноза для каждого актёра.
      // await new Promise((resolve) => {
      //   setTimeout(() => {
      //     resolve();
      //   }, 200);
      // });

      await this.modelPredict();
    },

    getCellIndex([prediction]) {
      return Math.round(prediction * this.field.length);
    },

    fill(index) {
      this.field.splice(index, 1, 1);
    },

    saveTraining({ label }) {
      this.learning.inputs.push(this.field);
      this.learning.labels.push([label]);
    },

    async modelFit() {
      await this.model.fit(
        tf.tensor2d(this.learning.inputs),
        tf.tensor2d(this.learning.labels),
      );

      this.games += 1;
      this.agentReset();
    },

    agentReset() {
      this.madeMoves = 0;
      this.field = [
        0, 0, 0,
        0, 0, 0,
        0, 0, 0,
      ];
    },
  },
};
</script>

<style scoped>
.TicTacToe {
  --quantity-rows: 3;
  --quantity-columns: 3;
  --square-size: 5rem;

  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  user-select: none;
}

.stat {
  position: absolute;
  top: 1rem;
  width: 100%;
  text-align: center;
  font-size: 1.2rem;
  color: white;
}

.field {
  display: grid;
  grid-template-rows: repeat(var(--quantity-rows), var(--square-size));
  grid-template-columns: repeat(var(--quantity-columns), var(--square-size));
  grid-gap: 0.5rem;
}

.cell {
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: seagreen;
}

.agent {
  font-size: 2rem;
}
</style>
