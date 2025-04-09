import Form from "@/components/Form";
import { ModalProps } from "@/types";

function Modal({ isOpen, onClose }: ModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-40 z-50">
      <div className="relative bg-white shadow-2xl rounded-lg w-[90vw] max-w-5xl h-[90vh] p-8 overflow-y-auto">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-xl font-bold text-gray-700"
        >
          ✕
        </button>

        <h2 className="text-2xl font-bold mb-6">
          Fill out extra information
        </h2>

        <Form onSave={onClose} />
      </div>
    </div>
  );
}

export default Modal;
