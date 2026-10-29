/*@
  requires b != 0;
  assigns \nothing;
  ensures \result == a / b;
*/
int divide(int a, int b)
{
	return a / b;
}
int main(){
	int a = 10;
    int b = 2;
    int c = divide(a, b);
    //@ assert c == 5;
}