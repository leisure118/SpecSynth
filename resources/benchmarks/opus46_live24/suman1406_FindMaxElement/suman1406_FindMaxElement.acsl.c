/*@
  requires n >= 1;
  requires \valid(arr+(0..n-1));
  ensures \forall integer i; 0 <= i < n ==> arr[i] <= \result;
  ensures \exists integer i; 0 <= i < n && arr[i] == \result;
  assigns \nothing;
*/
int findMax(int arr[], int n) {
    int max = arr[0];
    /*@
      loop invariant 1 <= i <= n;
      loop invariant \forall integer j; 0 <= j < i ==> arr[j] <= max;
      loop invariant \exists integer j; 0 <= j < i && arr[j] == max;
      loop assigns i, max;
      loop variant n - i;
    */
    for (int i = 1; i < n; i++) {
        if (arr[i] > max) {
            max = arr[i];
        }
    }
    return max;
}
int main(){
    int arr[] = {0, 1, 2, 3, 4};
    int n = sizeof(arr) / sizeof(arr[0]);
    int max = findMax(arr, n);
    //@ assert \forall integer i; 0 <= i < n ==> arr[i] <= max;
    return 0;
}
