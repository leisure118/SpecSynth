#include<stddef.h>
void reset(int* array,size_t length)
{
    for(size_t i =0;i<length;i++)   
  {
    array[i] = 0;
  }
} 
void main()
{
  int a[6] = {4,6,3,6,7,89};
  reset(a,6);
  //@ assert \forall integer i; 0<= i < 6 ==> a[i] == 0;
}