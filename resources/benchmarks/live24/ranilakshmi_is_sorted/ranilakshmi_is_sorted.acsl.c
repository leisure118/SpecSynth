/*@
  requires n >= 0;
  requires \valid(a + (0 .. n-1));
  assigns \nothing;
*/
int is_sorted(int a[],int n){
    /*@
      loop invariant 1 <= i <= n+1;
      loop invariant \forall integer j; 1 <= j < i ==> a[j] >= a[j-1];
      loop assigns i;
      loop variant n - i;
    */
    for (int i=1;i<n;i++){
        if (a[i-1]>a[i]){
            //@ assert \exists integer j; 1<=j<=i && a[j]< a[j-1];
            return 0;
        }
    }
    //@ assert \forall integer j; 1<=j<n ==> a[j]>=a[j-1];
    return 1;
}