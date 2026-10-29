/*@
  requires \valid(a + (0 .. n-1));
  assigns a[0 .. n-1];
  ensures \forall integer i; 0 <= i < n ==> a[i] == \old(a[i]) * 2;
*/
void arrayDouble(int *a, unsigned int n) {
    int p = 0;
    /*@
      loop invariant 0 <= p <= n;
      loop invariant \forall integer i; 0 <= i < p ==> a[i] == \at(a[i], LoopEntry) * 2;
      loop invariant \forall integer i; p <= i < n ==> a[i] == \at(a[i], LoopEntry);
      loop assigns p, a[0 .. n-1];
      loop variant n - p;
    */
    while (p < n) {
        a[p] = a[p] * 2;
        p = p + 1;
    } 
}
int main() {
    int arr[] = {0,1,2,3,4,5};
    arrayDouble(arr, 6);
    //@ assert arr[0] == 0;
    //@ assert arr[1] == 2;
    //@ assert arr[2] == 4;
    //@ assert arr[3] == 6;
    //@ assert arr[4] == 8;
    //@ assert arr[5] == 10;
}