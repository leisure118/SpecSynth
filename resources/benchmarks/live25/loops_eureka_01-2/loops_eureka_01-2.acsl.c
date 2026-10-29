int INFINITY = 899;
int main(){
  int nodecount = 5;
  int edgecount = 20;
  int source = 0;
  int Source[20] = {0,4,1,1,0,0,1,3,4,4,2,2,3,0,0,3,1,2,2,3};
  int Dest[20] = {1,3,4,1,1,4,3,4,3,0,0,0,0,2,3,0,2,1,0,4};
  int Weight[20] = {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19};
  int distance[5];
  int x,y;
  int i,j;
  /*@
    loop invariant 0 <= i <= nodecount;
    loop invariant \forall integer k; 0 <= k < i ==> distance[k] >= 0;
    loop assigns i, distance[0 .. nodecount-1];
    loop variant nodecount - i;
  */
  for(i = 0; i < nodecount; i++){
    if(i == source){
      distance[i] = 0;
    }
    else {
      distance[i] = INFINITY;
    }
  }
  /*@
    loop invariant 0 <= i <= nodecount;
    loop invariant \forall integer k; 0 <= k < nodecount ==> distance[k] >= 0;
    loop assigns i, j, x, y, distance[0 .. nodecount-1];
    loop variant nodecount - i;
  */
  for(i = 0; i < nodecount; i++)
    {
      /*@
        loop invariant 0 <= j <= edgecount;
        loop invariant \forall integer k; 0 <= k < nodecount ==> distance[k] >= 0;
        loop assigns j, x, y, distance[0 .. nodecount-1];
        loop variant edgecount - j;
      */
      for(j = 0; j < edgecount; j++)
	{
	  x = Dest[j];
	  y = Source[j];
	  if(distance[x] > distance[y] + Weight[j])
	    {
	      distance[x] = distance[y] + Weight[j];
	    }
	}
    }
  /*@
    loop invariant 0 <= i <= edgecount;
    loop invariant \forall integer k; 0 <= k < nodecount ==> distance[k] >= 0;
    loop assigns i, x, y;
    loop variant edgecount - i;
  */
  for(i = 0; i < edgecount; i++)
    {
      x = Dest[i];
      y = Source[i];
      if(distance[x] > distance[y] + Weight[i])
	{
	  return 0;
	}
    }
  /*@
    loop invariant 0 <= i <= nodecount;
    loop invariant \forall integer k; 0 <= k < nodecount ==> distance[k] >= 0;
    loop assigns i;
    loop variant nodecount - i;
  */
  for(i = 0; i < nodecount; i++)
    {
      //@ assert(distance[i]>=0);
    }
  return 0;
}
