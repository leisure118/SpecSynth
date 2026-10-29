/*@
  requires n >= 1;
  requires \valid(a + (0 .. n-1));
  assigns \nothing;
  ensures \forall integer j; 0 <= j < n ==> \result >= a[j];
  ensures \exists integer j; 0 <= j < n && \result == a[j];
*/
int arraymax(int* a, int n) {
  int i = 1;
  int max = a[0];
  /*@
    loop invariant 1 <= i <= n;
    loop invariant \forall integer j; 0 <= j < i ==> max >= a[j];
    loop invariant \exists integer j; 0 <= j < i && max == a[j];
    loop assigns i, max;
    loop variant n - i;
  */
  while (i < n) {
    if (max < a[i])
    max = a[i];
    i = i + 1;
  }
  return max;
}
void main() {
  int arr[5] = {1, 2, 3, 4, 5};
  int sum = arraymax(arr, 5);
  //@ assert sum == 5;
}