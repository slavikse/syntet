<template>
  <div class="TicTacToe">
    <div class="fields">
      <div class="stat">
        Сыграно игр: {{ games }} | Побед: X {{ victories.X }} - O {{ victories.O }}
      </div>

      <div
        v-for="(agent, agentIndex) in agents.X.concat(agents.O)"
        :key="agentIndex"
        class="field"
      >
        <div
          v-for="(cell, cellIndex) in agent.field"
          :key="`${agentIndex}:${cellIndex}`"
          :class="['cell', {
            'alive': agent.isAlive,
            cell,
            'victory': agent.isVictory,
          }]"
          @click="setSign(agent, cellIndex)"
        >
          {{ cell }}
          <!--{{ agent.rewards[cellIndex].toFixed(1) }}-->
        </div>
      </div>
    </div>

    <div class="duel-field">
      <div
        v-for="(cell, cellIndex) in duel.field"
        :key="cellIndex"
        :class="['duel-cell', { cell }]"
      >
        {{ cell }}
      </div>
    </div>
  </div>
</template>

<script>
// todo 2 Этап. Тренировка 2х сетей играть друг с другом.
// сталкивать сети между собой на 100 игр каждые 1000 игр.
// после 100 игр, каждая сеть получит наигранные веса для обучения.

// todo 3 Этап. Сохранение весов лучшей предобученной сети для игры с человеком.

// todo последовательности ходов

import * as tf from '@tensorflow/tfjs';
import { victoryCheckGroups as hasVictory } from './utils';

const isAutomatic = true;
const isDelay = false;

export default {
  name: 'TicTacToe',

  data() {
    return {
      modelX: tf.sequential(),
      modelO: tf.sequential(),
      trainingCount: { X: 0, O: 0 },
      training: {
        X: { inputs: [], labels: [] },
        O: { inputs: [], labels: [] },
      },
      agents: { X: [], O: [] },
      victories: { X: 0, O: 0 },

      fieldSize: 9,
      step: 1,
      games: 1,

      isDuel: false,
      duel: { // Настраивается в startDuel
        step: 1,
        field: [
          '', '', '',
          '', '', '',
          '', '', '',
        ],
      },
    };
  },

  async mounted() {
    this.setupModel({ model: this.modelX });
    this.setupModel({ model: this.modelO });

    this.agentsSetting({ sign: 'X' });
    this.agentsSetting({ sign: 'O' });

    if (isAutomatic) {
      await this.gameLoop();
    }
  },

  methods: {
    setupModel({ model }) {
      model.add(tf.layers.dense({
        // +1 - Количество ходов.
        inputShape: [this.fieldSize + 1],
        activation: 'sigmoid',
        units: 32,
      }));

      // model.add(tf.layers.dense({
      //   activation: 'sigmoid',
      //   units: 24,
      // }));

      model.add(tf.layers.dense({
        activation: 'sigmoid',
        units: this.fieldSize,
      }));

      model.compile({
        optimizer: 'adam',
        loss: 'meanSquaredError',
      });
    },

    agentsSetting({ sign }) {
      this.agents[sign] = [
        {
          sign,
          isAlive: true,
          isVictory: false,
          rewards: [
            0.1, 0.1, 0.1,
            0.1, 0.1, 0.1,
            0.1, 0.1, 0.1,
          ],
          field: [
            '', '', '',
            '', '', '',
            '', '', '',
          ],
        },
      ];
    },

    async gameLoop() {
      // console.log(this.isDuel, this.duel.step);

      if (this.isDuel) {
        // todo
        // await this.startDuel();
      } else {
        // this.isDuel = this.games % this.fieldSize === 0;
        await this.startTraining();
      }

      if (isDelay) {
        await new Promise((resolve) => setTimeout(resolve, 100));
      }

      this.games += 1;
      await this.gameLoop();
    },

    async startDuel() {
      await new Promise((resolve) => {
        const agents = this.agents.X.filter(({ isAlive }) => isAlive);
        let count = agents.length;

        agents.forEach(async (agent) => {
          await this.modelPredict({ model: this.modelX, agent });
          count -= 1;

          if (count === 0) {
            resolve();
          }
        });
      });

      await new Promise((resolve) => {
        const agents = this.agents.O.filter(({ isAlive }) => isAlive);
        let count = agents.length;

        agents.forEach(async (agent) => {
          await this.modelPredict({ model: this.modelO, agent });
          count -= 1;

          if (count === 0) {
            resolve();
          }
        });
      });

      if (this.duel.step === this.fieldSize) {
        await Promise.all([
          this.modelFit({ model: this.modelX, sign: 'X' }),
          this.modelFit({ model: this.modelO, sign: 'O' }),
        ]);

        this.isDuel = false;

        this.duel = {
          step: 1,
          field: [
            '', '', '',
            '', '', '',
            '', '', '',
          ],
        };
      } else {
        this.duel.step += 1;
      }
    },

    async startTraining() {
      await Promise.all(this.agents.X.filter(({ isAlive }) => isAlive)
        .map((agent) => this.modelPredict({ model: this.modelX, agent }))
        .concat(this.agents.O.filter(({ isAlive }) => isAlive)
          .map((agent) => this.modelPredict({ model: this.modelO, agent }))));

      if (this.step === this.fieldSize) {
        await Promise.all([
          this.modelFit({ model: this.modelX, sign: 'X' }),
          this.modelFit({ model: this.modelO, sign: 'O' }),
        ]);

        this.agentsSetting({ sign: 'X' });
        this.agentsSetting({ sign: 'O' });

        this.step = 1;
      } else {
        this.step += 1;
      }
    },

    /* eslint-disable no-confusing-arrow */
    async modelPredict({ model, agent }) {
      let stepInput;

      if (this.step <= 3) {
        stepInput = this.step / 3;
      } else {
        stepInput = 1 - (this.step / this.fieldSize);
      }

      const predictions = await model.predict(tf.tensor2d([agent.rewards.concat([stepInput])])).data();
      const cellIndex = predictions.indexOf(Math.max(...predictions));

      const { sign } = agent;
      const field = this.isDuel ? this.duel.field : agent.field;

      if (field[cellIndex].length === 0) {
        field.splice(cellIndex, 1, sign);
        agent.rewards = agent.rewards.map((weight) => weight + 0.1);

        const isWinner = hasVictory.horizontalGroup({ field, sign })
          || hasVictory.verticalGroup({ field, sign, start: 0, step: 2 })
          || hasVictory.obliquelyGroup({ field, sign });

        if (isWinner) {
          agent.isAlive = false;
          agent.isVictory = true;
          agent.rewards[cellIndex] = 0.99;

          this.saveTraining({
            input: field.map((cell) => cell === sign ? 0.9 : 0.1).concat([stepInput]),
            label: agent.rewards,
            sign,
          });

          console.log('isWinner', sign, this.isDuel);

          if (this.isDuel) {
            this.victories[sign] += 1;
          }
        } else {
          agent.rewards[cellIndex] = 0.5;

          this.saveTraining({
            input: field.map((cell) => cell === sign ? 0.5 : 0.05).concat([stepInput]),
            label: agent.rewards,
            sign,
          });
        }
      } else {
        agent.isAlive = false;
        agent.rewards[cellIndex] = 0.01;

        this.saveTraining({
          input: field.map((cell) => cell.length === 0 ? 0.05 : 0.01).concat([stepInput]),
          label: agent.rewards,
          sign,
        });
      }
    },

    saveTraining({ input, label, sign }) {
      this.training[sign].inputs.push(input);
      this.training[sign].labels.push(label);

      this.trainingCount[sign] += 1;
    },

    async modelFit({ model, sign }) {
      if (this.trainingCount[sign] > 0) {
        this.trainingCount[sign] = 0;

        await model.fit(
          tf.tensor2d(this.training[sign].inputs),
          tf.tensor2d(this.training[sign].labels),
          { epochs: 1 },
        );

        this.training[sign].inputs = [];
        this.training[sign].labels = [];
      }
    },

    setSign(agent, cellIndex) {
      const { sign } = agent;

      if (!isAutomatic && agent.field[cellIndex].length === 0) {
        agent.field.splice(cellIndex, 1, sign);
        agent.rewards = agent.rewards.map((weight) => weight + 0.1);

        const isWinner = hasVictory.horizontalGroup({ field: agent.field, sign })
          || hasVictory.verticalGroup({ field: agent.field, sign, start: 0, step: 2 })
          || hasVictory.obliquelyGroup({ field: agent.field, sign });

        if (isWinner) {
          agent.isAlive = false;
          agent.isVictory = true;
        }

        console.log('isWinner', isWinner);
      }
    },
  },
};
</script>

<style scoped>
.TicTacToe {
  --quantity-rows: 3;
  --quantity-columns: 3;
  --square-size: 64px;

  position: relative;
  margin: 200px 0 0 200px;
  display: flex;
  user-select: none;
}

.fields {
  position: relative;
  display: flex;
}

.stat {
  position: absolute;
  top: 0;
  margin-top: -20px;
  width: 100%;
  text-align: center;
  color: white;
}

.field {
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
  font-size: 30px;
  background-color: seagreen;
}

.cell.alive {
}

.cell.X {
  background-color: black;
}

.cell.O {
  color: black;
  background-color: white;
}

.cell.victory {
  background-color: gold;
}

.duel-field {
  margin: 5px;
  display: grid;
  grid-template-rows: repeat(var(--quantity-rows), var(--square-size));
  grid-template-columns: repeat(var(--quantity-columns), var(--square-size));
  grid-gap: 1px;
}

.duel-cell {
  color: black;
  background-color: aliceblue;
}
</style>
