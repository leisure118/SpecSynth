/*@
  requires n >= 0;
  requires \valid(arr + (0 .. n-1));
  assigns \nothing;
  ensures -1 <= \result < n;
  ensures \result == -1 ==> \forall integer j; 0 <= j < n ==> arr[j] != x;
  ensures \result >= 0 ==> (\forall integer k; 0 <= k < \result ==> arr[k] != x) && arr[\result] == x;
*/
int array_find(int* arr, int n, int x) {
    int i = 0;
    /*@
      loop invariant 0 <= i <= n;
      loop invariant \forall integer j; 0 <= j < i ==> arr[j] != x;
      loop assigns i;
      loop variant n - i;
    */
    for (i = 0; i < n; i++) {
        if (arr[i] == x) {
            return i;
        }
    }
    return -1;
}
void main() {
    int arr[5] = {1, 2, 3, 4, 5};
    int index = array_find(arr, 5, 3);
    //@ assert index == 2;
}