#include<stddef.h>
/*@
  requires \valid(array+(0 .. length-1));
  assigns array[0 .. length-1];
  ensures \forall integer j; 0 <= j < length ==> array[j] == 0;
*/
void reset(int* array,size_t length){
/*@
  loop invariant 0 <= i <= length;
  loop invariant \forall integer j; 0 <= j < i ==> array[j] == 0;
  loop assigns i, array[0 .. length-1];
  loop variant length - i;
*/
for(size_t i=0;i<length;i++){
array[i]=0;}
}
int main(){
int a[]={1,2,3,4,5};
reset(a,5);
//@ assert a[0] == 0;
//@ assert a[1] == 0;
//@ assert a[2] == 0;
//@ assert a[3] == 0;
//@ assert a[4] == 0;
}