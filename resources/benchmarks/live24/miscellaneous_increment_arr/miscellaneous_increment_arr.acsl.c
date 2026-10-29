/*@
  requires n >= 0;
  requires \valid(arr + (0 .. n-1));
  assigns arr[0 .. n-1];
  ensures \forall integer j; 0 <= j < n ==> arr[j] == \old(arr[j]) + c;
*/
void increment_array_by(int* arr, int n, int c) {
    /*@
      loop invariant 0 <= i <= n;
      loop invariant \forall integer j; 0 <= j < i ==> arr[j] == \at(arr[j], Pre) + c;
      loop invariant \forall integer j; i <= j < n ==> arr[j] == \at(arr[j], Pre);
      loop assigns i, arr[0 .. n-1];
      loop variant n - i;
    */
    for (int  i = 0; i < n; i++) {
        arr[i] = arr[i] + c;
    }
}
void main() {
    int arr[5] = {1, 2, 3, 4, 5};
    increment_array_by(arr, 5, 2);
    //@ assert arr[0] == 3;
    //@ assert arr[1] == 4;
    //@ assert arr[2] == 5;
    //@ assert arr[3] == 6;
    //@ assert arr[4] == 7;
}
