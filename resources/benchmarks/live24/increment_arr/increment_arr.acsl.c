/*@
  requires n >= 0;
  requires \valid(arr + (0 .. n-1));
  assigns arr[0 .. n-1];
  ensures \forall integer k;
  0 <= k < n ==> arr[k] == \old(arr[k]) + c;
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
     //@ assert \forall integer k; 0 <= k < n ==> arr[k] == (\at(arr[k], Pre) + c);
}
int main(){
    int arr[10] = {1,2,3,4,5,6,7,8,9,10};
    Label_a:
    increment_array_by(arr, 10, 1);
    //@ assert \forall integer k; 0 <= k < 10 ==> arr[k] == (\at(arr[k], Label_a) + 1);
}