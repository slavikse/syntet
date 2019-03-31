<template>
  <div>
    <div class="stat generation">
      Живых: {{ aliveCount }} | Поколений: {{ generation }} | Побед: {{ win }}
      <br>
      Шагов: {{ stepCount }} | Максимальное значение ячейки: {{ maximumCellValue }}
    </div>

    <div
      ref="Square"
      class="Square"
      tabindex="0"
    >
      <div class="cells field">
        <div
          v-for="(cellValue, index) in field"
          :key="index"
          :data-cell-value="cellValue"
          :class="['cell', { 'available': cellValue !== 0 }]"
        >
          <div
            v-if="cellValue === 1"
            class="starting-checkpoint"
          >
            СТАРТ
          </div>

          <div
            v-if="cellValue === maxCellValues"
            class="finishing-checkpoint"
          >
            ФИНИШ
          </div>
        </div>
      </div>

      <div class="actors field">
        <div
          v-for="(actor, index) in actors"
          :key="index"
          :style="{
            gridRow: actor.y,
            gridColumn: actor.x,
          }"
          class="actor-container"
        >
          <div
            v-if="actor.alive"
            :ref="`actors_${index}`"
            class="actor"
          >
            <div class="actor-icon">
              🐥
            </div>

            <!-- Усики сканирующие клетку во всех четырёх сторонах. -->
            <div class="antenna jump-top" />
            <div class="antenna jump-right" />
            <div class="antenna jump-bottom" />
            <div class="antenna jump-left" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as tf from '@tensorflow/tfjs';
import cloneDeep from 'clone-deep';

const actorsDefault = [];
const actorsCount = 3000;
// Каждый N будет исследователем.
const eachNumber = 300;

/* eslint-disable no-plusplus */
for (let i = 0; i < actorsCount; i++) {
  actorsDefault.push({
    alive: true,
    x: 2,
    y: 2,
    step: 0,
    style: undefined,
  });
}

export default {
  name: 'Square',

  data() {
    return {
      model: tf.sequential(),
      // Очищаемое поколение всех актёров перед следующим поколением.
      preTraining: {
        inputs: [],
        labels: [],
      },
      // Набор лучших поколений из нескольких в preTraining.
      training: {
        // x, y - Нормализованные координаты актёра.
        // step - Количество шагов, сделанных от стартовой позиции.
        inputs: [],
        // [1, 0, 0, 0] - Пойти на север (north).
        // [0, 1, 0, 0] - Пойти на восток (east).
        // [0, 0, 1, 0] - Пойти на юг (south).
        // [0, 0, 0, 1] - Пойти на запад (west).
        labels: [],
      },
      generation: 0,
      win: 0,

      actors: [],
      maximumCellValue: 0,

      fieldStyle: undefined,
      // Игровая область обязательно квадратной формы, для Math.sqrt(this.field.length).
      // Обязательно между доступным путём, должно быть 2 запретных ячейки из за усиков.
      // 0 - Запретная территория.
      // [1..N) - Проходная территория.
      // N - Финишная точка.
      // @formatter:off
      /* eslint-disable no-multi-spaces */
      field: [
        0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
        0,  1,  0,  0,  0,  0,  0,  0,  0, 45, 44, 43,  0,
        0,  2,  0,  0,  0,  0,  0,  0,  0,  0,  0, 42,  0,
        0,  3,  0,  0,  8,  9, 10, 11,  0,  0,  0, 41,  0,
        0,  4,  5,  6,  7,  0,  0, 12,  0,  0,  0, 40,  0,
        0,  0,  0,  0,  0,  0,  0, 13,  0,  0,  0, 39,  0,
        0,  0,  0,  0,  0,  0, 15, 14,  0,  0,  0, 38,  0,
        0,  0,  0,  0,  0,  0, 16,  0,  0,  0,  0, 37,  0,
        0,  0, 21, 20, 19, 18, 17,  0,  0,  0,  0, 36,  0,
        0,  0, 22,  0,  0,  0,  0,  0,  0, 33, 34, 35,  0,
        0,  0, 23,  0,  0,  0,  0,  0,  0, 32,  0,  0,  0,
        0,  0, 24, 25, 26, 27, 28, 29, 30, 31,  0,  0,  0,
        0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
      ],
      // @formatter:on
      /* eslint-enable no-multi-spaces */
      maxCellValues: 45,
      maxStep: 45 * 2,
      size: -1,
    };
  },

  computed: {
    aliveCount() {
      return this.actors.filter(({ alive }) => alive).length || 0;
    },

    stepCount() {
      return Math.max(0, ...this.actors.filter(({ alive }) => alive).map(({ step }) => step));
    },
  },

  async mounted() {
    this.fieldSetting();
    this.setupModel();

    await this.actorsReset();
    await this.modelPredict();
  },

  methods: {
    fieldSetting() {
      this.fieldStyle = this.$refs.Square.style;
      this.size = Math.sqrt(this.field.length);

      this.fieldStyle.setProperty('--quantity-rows', this.size);
      this.fieldStyle.setProperty('--quantity-columns', this.size);
    },

    setupModel() {
      this.model.add(tf.layers.dense({
        // Описание в training.inputs.
        inputShape: [3],
        activation: 'sigmoid',
        units: 12,
      }));

      // this.model.add(tf.layers.dense({
      //   activation: 'sigmoid',
      //   units: 64,
      // }));

      // this.model.add(tf.layers.dense({
      //   activation: 'sigmoid',
      //   units: 128,
      // }));

      this.model.add(tf.layers.dense({
        activation: 'sigmoid',
        // [north, east, south, west] - Прогноз стороны для передвижения.
        units: 4,
      }));

      this.model.compile({
        optimizer: tf.train.adam(0.01),
        loss: 'meanSquaredError',
        // metrics: ['accuracy'],
      });
    },

    async actorsReset() {
      this.actors = cloneDeep(actorsDefault);
      await this.$nextTick();

      this.actors.forEach((actor, index) => {
        const [{ style }] = this.$refs[`actors_${index}`];
        actor.style = style;
      });
    },

    async modelPredict() {
      await Promise.all(this.actors.map(async (actor, index) => {
        if (actor.alive) {
          const prediction = await this.model.predict(tf.tensor2d([
            [
              actor.x / this.size,
              actor.y / this.size,
              actor.step / this.maxStep,
            ],
          ])).data();

          const action = this.getAction(prediction, index);
          this[action](actor);

          await this.availabilityCheck(actor);
        }

        // Замедление прогноза для каждого актёра.
        // await new Promise((resolve) => {
        //   setTimeout(() => {
        //     resolve();
        //   }, 100);
        // });
      }));

      await this.modelPredict();
    },

    getAction([jumpTop, jumpRight, jumpBottom, jumpLeft], index) {
      // Сбрасывает некоторые решения, делая их случайными.
      if (index % eachNumber === 0) {
        jumpTop = Math.random();
        jumpRight = Math.random();
        jumpBottom = Math.random();
        jumpLeft = Math.random();
      }

      // console.log(
      //   'Top', jumpTop.toFixed(10),
      //   'Right', jumpRight.toFixed(10),
      //   'Bottom', jumpBottom.toFixed(10),
      //   'Left', jumpLeft.toFixed(10),
      // );

      let maximum = jumpTop;
      let action = 'jumpTop';

      if (jumpRight > maximum) {
        maximum = jumpRight;
        action = 'jumpRight';
      }

      if (jumpBottom > maximum) {
        maximum = jumpBottom;
        action = 'jumpBottom';
      }

      if (jumpLeft > maximum) {
        maximum = jumpLeft;
        action = 'jumpLeft';
      }

      return action;
    },

    jumpTop(actor) {
      actor.y -= 1;
    },

    jumpRight(actor) {
      actor.x += 1;
    },

    jumpBottom(actor) {
      actor.y += 1;
    },

    jumpLeft(actor) {
      actor.x -= 1;
    },

    async availabilityCheck(actor) {
      // Смещение на -1: Сетка начинается с 1, а значения в массиве начинаются с 0.
      const normalY = actor.y - 1;
      const normalX = actor.x - 1;
      const cellValue = this.field[normalY * this.size + normalX];

      // Очень важно передавать значения в label[] в таком же порядке!
      const label = this.getAntennaCellValues({ normalX, normalY });

      // Сброс при успешном прохождении.
      let isReset = false;

      // Ввод максимального шага.
      if (cellValue > this.maximumCellValue) {
        this.maximumCellValue = cellValue;
      }

      switch (true) {
        case cellValue === 0:
          actor.alive = false;
          break;

        case actor.step === this.maxStep:
          actor.alive = false;
          break;

        case cellValue > 0 && cellValue < this.maxCellValues:
          actor.step += 1;
          break;

        case cellValue === this.maxCellValues:
          actor.alive = false;
          isReset = true;
          console.log('ФИНИШ!', actor.x, actor.y);

          actor.step += 1;
          this.win += 1;
          break;

        default:
      }

      this.savePreTraining({ actor, label });

      const living = this.actors.filter(({ alive }) => alive).length;

      if (living === 0) {
        await this.modelFit();
      }

      if (isReset) {
        await this.actorsReset();
      }
    },

    // Получение значения ячейки, чем дальше ячейка от старта, тем больше там значение.
    getAntennaCellValues({ normalX, normalY }) {
      // 0 - когда выходит за пределы поля (дальше пути нет).
      const top = this.field[(normalY - 1) * this.size + normalX] || 0;
      const right = this.field[normalY * this.size + (normalX + 1)] || 0;
      const bottom = this.field[(normalY + 1) * this.size + normalX] || 0;
      const left = this.field[normalY * this.size + (normalX - 1)] || 0;

      return [
        top / this.maxCellValues,
        right / this.maxCellValues,
        bottom / this.maxCellValues,
        left / this.maxCellValues,
      ];
    },

    savePreTraining({ actor, label }) {
      this.preTraining.inputs.push([
        actor.x / this.size,
        actor.y / this.size,
        actor.step / this.maxStep,
      ]);

      this.preTraining.labels.push(label);
    },

    async modelFit() {
      const {
        inputs1,
        labels1,

        inputs2,
        labels2,

        inputs3,
        labels3,
      } = this.getTheBest();

      this.training.inputs.push(...inputs1, ...inputs2, ...inputs3);
      this.training.labels.push(...labels1, ...labels2, ...labels3);

      // await this.model.fit(
      //   tf.tensor2d(this.preTraining.inputs),
      //   tf.tensor2d(this.preTraining.labels),
      // );

      this.preTraining = { inputs: [], labels: [] };

      await this.model.fit(
        tf.tensor2d(this.training.inputs),
        tf.tensor2d(this.training.labels),
      );

      this.generation += 1;
      await this.actorsReset();
    },

    getTheBest() {
      let third = 0;
      let second = 0;
      let first = 0;

      let thirdIndex = 0;
      let secondIndex = 0;
      let firstIndex = 0;

      this.preTraining.inputs.forEach(([, , step], index) => {
        switch (true) {
          case step > first:
            third = second;
            second = first;
            first = step;

            thirdIndex = secondIndex;
            secondIndex = firstIndex;
            firstIndex = index;
            break;

          case step > second:
            third = second;
            second = step;

            thirdIndex = secondIndex;
            secondIndex = index;
            break;

          case step > third:
            third = step;

            thirdIndex = index;
            break;

          default:
        }
      });

      // console.log('third', third);
      // console.log('second', second);
      // console.log('first', first);

      // console.log('thirdIndex', thirdIndex);
      // console.log('secondIndex', secondIndex);
      // console.log('firstIndex', firstIndex);

      const inputs1 = this.preTraining.inputs.slice(first, first + 1);
      const labels1 = this.preTraining.labels.slice(firstIndex, firstIndex + 1);

      const inputs2 = this.preTraining.inputs.slice(second, second + 1);
      const labels2 = this.preTraining.labels.slice(secondIndex, secondIndex + 1);

      const inputs3 = this.preTraining.inputs.slice(third, third + 1);
      const labels3 = this.preTraining.labels.slice(thirdIndex, thirdIndex + 1);

      return {
        inputs1,
        labels1,

        inputs2,
        labels2,

        inputs3,
        labels3,
      };
    },
  },
};
</script>

<style scoped>
.Square {
  --quantity-rows: -1;
  --quantity-columns: -1;
  --column-width: 3rem;

  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  outline: none;
  user-select: none;
}

.stat {
  position: absolute;
  z-index: 1;
  font-size: 1.2rem;
  color: white;
}

.generation {
  margin-top: 1rem;
  width: 100%;
  text-align: center;
}

.cells {
}

.cell {
  position: relative;
  display: flex;
  background-color: #222;
}

.available {
  background-color: darkcyan;
}

.starting-checkpoint,
.finishing-checkpoint {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: 100%;
  line-height: 0.9;
  font-size: 0.7rem;
  font-weight: bold;
  background-color: seagreen;
  outline: 0.5rem dashed seagreen;
}

.field {
  display: grid;
  grid-template-rows: repeat(var(--quantity-rows), var(--column-width));
  grid-template-columns: repeat(var(--quantity-columns), var(--column-width));
  grid-gap: 0.5rem;
}

.actors {
  position: absolute;
}

.actor-container {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
}

.actor {
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: yellow;
  outline: 0.5rem dashed yellow;
}

.actor-icon {
  font-size: 2.4rem;
}

.antenna {
  position: absolute;
  height: 2px;
  width: 1.5rem;
  background-color: white;
}

.jump-top {
  top: -1.3rem;
  transform: rotate(90deg);
}

.jump-right {
  right: -2rem;
  transform: rotate(180deg);
}

.jump-bottom {
  bottom: -1.3rem;
  transform: rotate(270deg);
}

.jump-left {
  left: -2rem;
}
</style>
