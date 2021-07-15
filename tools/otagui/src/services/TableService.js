export function TableSort(arr, key, sortOrder, offset, limit) {
  let orderNumber = 1
  if (sortOrder==="desc") {
    orderNumber = -1
  }
  return arr.sort(function(a, b) {
    var keyA = a[key],
      keyB = b[key];
    if (keyA < keyB) return -1*orderNumber;
    if (keyA > keyB) return 1*orderNumber;
    return 0;
  }).slice(offset, offset + limit);
}