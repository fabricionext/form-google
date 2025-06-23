document.addEventListener('DOMContentLoaded', function () {
  const deleteButtons = document.querySelectorAll('.confirm-delete');
  deleteButtons.forEach(button => {
    button.addEventListener('click', function (event) {
      const confirmation = confirm(
        'Tem certeza que deseja excluir esta autoridade? Esta ação não pode ser desfeita.'
      );
      if (!confirmation) {
        event.preventDefault();
      }
    });
  });
});
