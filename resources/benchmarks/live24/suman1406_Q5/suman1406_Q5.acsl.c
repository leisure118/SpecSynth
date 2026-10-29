#include <limits.h>
/*@
  requires n >= 0;
  requires \valid(a+(0 .. n-1));
  requires \valid(b+(0 .. n-1));
  assigns \nothing;
  ensures \result == 1 <==> (\forall integer j; 0 <= j < n ==> a[j] == b[j]);
  ensures \result == 0 || \result == 1;
*/
int equ(int a[], int b[], int n)
{
    /*@
      loop invariant 0 <= i <= n;
      loop invariant \forall integer j; 0 <= j < i ==> a[j] == b[j];
      loop assigns i;
      loop variant n - i;
    */
    for (int i = 0; i < n; i++)
    {
        if (a[i] != b[i])
        {
            return 0;
        }
    }
    return 1;
}
int main(){
    int a[10]={1,2,3,4,5,6,7,8,9,10};
    int b[10]={1,2,3,4,5,6,7,8,9,10};
    int c[10]={1,2,3,4,5,6,7,8,9,11};

    int res=equ(a,b,10);
    int res1=equ(a,c,10);
    //@ assert res==1;
    //@ assert res1==0;
}