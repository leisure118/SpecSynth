#include<stddef.h>
void reset(int* array,size_t length){
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