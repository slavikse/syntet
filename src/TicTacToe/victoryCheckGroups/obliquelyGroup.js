import verticalGroup from './verticalGroup';

// Выигрышные наборы для третьей группы:
//  1.  2.
// X** **X
// *X* *X*
// **X X**

// Проверка 1 и 2 наборов.
export default function obliquelyGroup({ field, sign }) {
  return verticalGroup({ field, sign, start: 0, step: 3 })
    || verticalGroup({ field, sign, start: 2, step: 1 });
}
