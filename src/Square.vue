<template>
  <div>
    <div class="stat time">
      Секунд: {{ duration }}
    </div>

    <div class="stat generation">
      Поколений: {{ generation }} | Побед: {{ win }}
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
const actorsCount = 10;

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
      time: Date(),
      duration: 0,

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
      fieldStyle: undefined,
      // @formatter:on
      /* eslint-enable no-multi-spaces */
      maxCellValues: 45,
      maxStep: 45 * 3,
      size: -1,
    };
  },

  async mounted() {
    // Timer.
    setInterval(() => {
      this.time = Date();
      this.duration += 1;
    }, 1000);

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
        units: 256,
      }));

      this.model.add(tf.layers.dense({
        activation: 'sigmoid',
        units: 256,
      }));

      this.model.add(tf.layers.dense({
        activation: 'sigmoid',
        // [north, east, south, west] - Прогноз стороны для передвижения.
        units: 4,
      }));

      this.model.compile({
        optimizer: tf.train.adam(0.005),
        loss: 'meanSquaredError',
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
      /* eslint-disable no-restricted-syntax */
      for await (const actor of this.actors) {
        if (actor.alive) {
          const prediction = await this.model.predict(tf.tensor2d([
            [
              actor.x / this.size,
              actor.y / this.size,
              actor.step / this.maxStep,
            ],
          ])).data();

          const action = this.getAction(prediction);
          this[action](actor);

          await this.availabilityCheck(actor);
        }

        // Замедление прогноза для каждого актёра.
        // await new Promise((resolve) => {
        //   setTimeout(() => {
        //     resolve();
        //   }, 500);
        // });
      }

      await this.modelPredict();
    },

    getAction([jumpTop, jumpRight, jumpBottom, jumpLeft]) {
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
      const [top, right, bottom, left] = this.getAntennaCellValues({ normalX, normalY });

      const label = [
        top / this.maxCellValues,
        right / this.maxCellValues,
        bottom / this.maxCellValues,
        left / this.maxCellValues,
      ];

      // Сброс при успешном прохождении.
      let isReset = false;

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

        // todo особый
        case cellValue === this.maxCellValues:
          actor.alive = false;
          isReset = true;
          // todo выбирать лучших для обучения
          console.log('ФИНИШ!', actor.x, actor.y);

          actor.step += 1;
          this.win += 1;
          break;

        default:
      }

      // Для проверки, куда актёр пришёл.
      // console.log(`x: ${x}, y: ${y}, s: ${this.actor.step}, v: ${cellValue}, l: ${label}`);
      // console.log(`top: ${top}, right: ${right}, bottom: ${bottom}, left: ${left}`);

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

      return [top, right, bottom, left];
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
      let maxStep = 0;
      let bestIndex = 0;

      // todo выбирать несколько лучших для обучения.
      // 3 элемент при сохранении в savePreTraining.
      this.preTraining.inputs.forEach(([, , step], index) => {
        // todo для нахождения одного лучшего.
        if (step > maxStep) {
          maxStep = step;
          bestIndex = index;
        }
      });

      // console.log('maxStep', maxStep);
      // console.log('bestIndex', bestIndex);
      // console.log('preTraining.inputs', this.preTraining.inputs[bestIndex]);
      // console.log('preTraining.labels', this.preTraining.labels[bestIndex]);
      const preInputs = this.preTraining.inputs.slice(bestIndex, 1);
      const preLabels = this.preTraining.labels.slice(bestIndex, 1);
      // console.log('preInputs', preInputs);
      // console.log('preLabels', preLabels);
      this.preTraining = { inputs: [], labels: [] };

      this.training.inputs.push(...preInputs);
      this.training.labels.push(...preLabels);

      await this.model.fit(
        tf.tensor2d(this.training.inputs),
        tf.tensor2d(this.training.labels),
      );

      this.generation += 1;
      await this.actorsReset();
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

.time {
  margin-top: 3rem;
  width: 100%;
  text-align: center;
}

.generation {
  margin-top: 5rem;
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
