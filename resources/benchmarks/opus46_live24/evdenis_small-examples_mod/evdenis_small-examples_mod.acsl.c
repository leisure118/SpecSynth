/*@
  requires b != 0;
  assigns \nothing;
  ensures \result == a % b;
*/
int mod(int a, int b)
{
	return a % b;
}
int main(){
    int a = 10000;
    int b = 3;
    int c = mod(a,b);
    //@ assert c == 1;
}